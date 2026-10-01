from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.db.models import F, Q
from django.db.models.functions import Coalesce
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, View
from django.shortcuts import render, redirect
from django.utils import timezone
import uuid
from .forms import CheckoutForm, CouponForm, RefundForm
from .models import Item, OrderItem, Order, BillingAddress, Payment, Coupon, Refund, Category, StoreSettings, LegalPage, ContactMessage
from django.http import HttpResponseRedirect
# Create your views here.
import random
import string


def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))


class StockUnavailable(Exception):
    pass


def _current_cart(request):
    order = None
    lines = []
    if request.user.is_authenticated:
        order = Order.objects.filter(
            user=request.user, ordered=False
        ).prefetch_related('items__item').order_by('-pk').first()
        if order:
            for order_item in order.items.all():
                if not order_item.item_id:
                    continue
                item = order_item.item
                unit_price = order_item.get_final_price() / order_item.quantity
                lines.append({
                    'item': item,
                    'quantity': order_item.quantity,
                    'unit_price': unit_price,
                    'line_total': order_item.get_final_price(),
                    'order_item': order_item,
                })
        return order, lines

    cart = request.session.get('cart', {})
    if not isinstance(cart, dict):
        cart = {}
    item_ids = []
    quantities = {}
    for item_id, raw_quantity in cart.items():
        try:
            quantity = int(raw_quantity)
            item_ids.append(int(item_id))
            quantities[int(item_id)] = quantity
        except (TypeError, ValueError):
            continue

    products = Item.objects.filter(pk__in=item_ids, is_active=True)
    found_ids = set()
    for item in products:
        found_ids.add(item.pk)
        quantity = quantities[item.pk]
        if quantity < 1:
            continue
        unit_price = item.discount_price if item.discount_price is not None else item.price
        lines.append({
            'item': item,
            'quantity': quantity,
            'unit_price': unit_price,
            'line_total': unit_price * quantity,
            'order_item': None,
        })
    request.session['cart'] = {
        str(item_id): quantity for item_id, quantity in quantities.items()
        if item_id in found_ids and quantity > 0
    }
    return order, lines


def _cart_totals(lines, order=None):
    store = StoreSettings.get_solo()
    subtotal = sum(line['line_total'] for line in lines)
    if order and order.coupon_id:
        subtotal = max(0, subtotal - order.coupon.amount)
    shipping = 0 if subtotal >= store.free_shipping_threshold and subtotal else store.shipping_fee
    return {
        'subtotal': subtotal,
        'shipping': shipping,
        'total': subtotal + shipping,
        'store_settings': store,
    }


class PaymentView(View):
    def get(self, request, *args, **kwargs):
        messages.info(request, 'Le paiement accepté est le paiement à la livraison.')
        return redirect('core:checkout')

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


class HomeView(ListView):
    template_name = "index.html"
    context_object_name = 'items'
    paginate_by = 8

    def get_queryset(self):
        return Item.objects.filter(is_active=True).order_by('-pk')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)[:6]
        context['featured_items'] = Item.objects.filter(is_active=True).order_by('-pk')[:8]
        context['new_items'] = Item.objects.filter(is_active=True).order_by('-pk')[:4]
        context['promo_items'] = Item.objects.filter(is_active=True, discount_price__isnull=False)[:4]
        return context


class OrderSuccessView(View):
    template_name = 'order_success.html'

    def get(self, request, *args, **kwargs):
        ref_code = kwargs.get('ref_code')
        order = get_object_or_404(
            Order.objects.prefetch_related('items__item'), ref_code=ref_code)
        context = {
            'ref_code': ref_code,
            'order': order,
            'customer': {
                'full_name': order.customer_name,
                'phone_number': order.phone_number,
                'city': order.city,
                'street_address': order.delivery_address,
            },
        }
        return render(request, self.template_name, context)


class OrderSummaryView(View):
    def get(self, request, *args, **kwargs):
        order, lines = _current_cart(request)
        context = {'order': order, 'cart_lines': lines}
        context.update(_cart_totals(lines, order))
        return render(request, 'order_summary.html', context)


class ShopView(ListView):
    model = Item
    paginate_by = 8
    template_name = "shop.html"

    def get_queryset(self):
        queryset = Item.objects.filter(is_active=True).select_related('category')
        query = self.request.GET.get('q', '').strip()
        category_slug = self.request.GET.get('category', '').strip()
        sort = self.request.GET.get('sort', 'newest')

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(description_long__icontains=query)
                | Q(description_short__icontains=query)
            )

        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        if sort == 'price_asc':
            queryset = queryset.annotate(
                effective_price=Coalesce('discount_price', 'price')
            ).order_by('effective_price', 'pk')
        elif sort == 'price_desc':
            queryset = queryset.annotate(
                effective_price=Coalesce('discount_price', 'price')
            ).order_by('-effective_price', 'pk')
        elif sort == 'newest':
            queryset = queryset.order_by('-pk')
        else:
            queryset = queryset.order_by('-pk')

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True).order_by('title')
        context['query'] = self.request.GET.get('q', '')
        context['selected_category'] = self.request.GET.get('category', '')
        context['sort'] = self.request.GET.get('sort', 'newest')
        return context


class ItemDetailView(DetailView):
    model = Item
    template_name = 'product_page.html'

    def get_queryset(self):
        return Item.objects.filter(is_active=True).select_related(
            'category').prefetch_related('gallery_images')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = self.object
        context['related_items'] = Item.objects.filter(
            category=item.category,
            is_active=True,
        ).exclude(pk=item.pk)[:4]
        context['recent_items'] = Item.objects.filter(is_active=True).exclude(pk=item.pk).order_by('-pk')[:4]
        return context


# class CategoryView(DetailView):
#     model = Category
#     template_name = "category.html"

class CategoryView(View):
    def get(self, *args, **kwargs):
        category = get_object_or_404(
            Category, slug=self.kwargs['slug'], is_active=True)
        item = Item.objects.filter(
            category=category, is_active=True).select_related('category').order_by('-pk')
        context = {
            'object_list': item,
            'categories': Category.objects.filter(is_active=True).order_by('title'),
            'active_category': category,
            'category_title': category.title,
            'category_description': category.description,
            'category_image': category.image,
            'query': '',
            'sort': 'newest',
            'selected_category': category.slug,
        }
        return render(self.request, 'shop.html', context)


class CheckoutView(View):
    template_name = 'checkout.html'

    def build_form(self, data=None, initial=None):
        form = CheckoutForm(data=data, initial=initial)

        cities = [
            city.strip()
            for city in StoreSettings.get_solo().cities.splitlines()
            if city.strip()
        ]

        form.fields['city'].choices = (
            [('', 'Sélectionnez votre ville')]
            + [(city, city) for city in cities]
            + [('other', 'Autre ville')]
        )

        return form

    def render_checkout(self, request, form, order, lines, status=200):
        context = {
            'form': form,
            'order': order,
            'cart_lines': lines,
        }

        context.update(_cart_totals(lines, order))

        return render(
            request,
            self.template_name,
            context,
            status=status
        )

    def get(self, request, *args, **kwargs):
        order, lines = _current_cart(request)

        if not lines:
            messages.info(request, 'Votre panier est vide.')
            return redirect('core:shop')

        submission_key = request.session.get('checkout_submission_key')

        if not submission_key:
            submission_key = uuid.uuid4().hex
            request.session['checkout_submission_key'] = submission_key

        return self.render_checkout(
            request,
            self.build_form(
                initial={'submission_key': submission_key}
            ),
            order,
            lines,
        )

    def post(self, request, *args, **kwargs):
        order, lines = _current_cart(request)

        form = self.build_form(data=request.POST)

        if not form.is_valid():
            return self.render_checkout(
                request,
                form,
                order,
                lines,
                status=400
            )

        submission_key = form.cleaned_data['submission_key']

        session_key = request.session.get('checkout_submission_key')
        completed_key = request.session.get('last_checkout_submission_key')

        if submission_key not in (session_key, completed_key):
            form.add_error(
                None,
                'Cette session de commande a expiré. Réessayez.'
            )

            return self.render_checkout(
                request,
                form,
                order,
                lines,
                status=400
            )

        existing_order = Order.objects.filter(
            idempotency_key=submission_key
        ).first()

        if existing_order:
            return redirect(
                'core:order-success',
                ref_code=existing_order.ref_code
            )

        if form.cleaned_data['website']:
            form.add_error(
                None,
                'Impossible de traiter cette demande.'
            )

            return self.render_checkout(
                request,
                form,
                order,
                lines,
                status=400
            )

        if not lines:
            form.add_error(
                None,
                'Votre panier est vide.'
            )

            return self.render_checkout(
                request,
                form,
                order,
                lines,
                status=400
            )

        item_ids = [
            line['item'].pk
            for line in lines
        ]

        try:
            with transaction.atomic():

                locked_items = Item.objects.select_for_update().filter(
                    pk__in=item_ids,
                    is_active=True
                ).order_by('pk')

                items_by_id = {
                    item.pk: item
                    for item in locked_items
                }

                # Vérification du stock
                for line in lines:

                    item = items_by_id.get(
                        line['item'].pk
                    )

                    if item is None:
                        form.add_error(
                            None,
                            'Un produit de votre panier n’est plus disponible.'
                        )

                        return self.render_checkout(
                            request,
                            form,
                            order,
                            lines,
                            status=409
                        )

                    if line['quantity'] > item.stock:
                        form.add_error(
                            None,
                            'Stock insuffisant pour ce produit. '
                            'Veuillez réduire la quantité.'
                        )

                        return self.render_checkout(
                            request,
                            form,
                            order,
                            lines,
                            status=409
                        )

                # Calcul du sous-total
                subtotal = sum(
                    (
                        item.discount_price
                        if item.discount_price is not None
                        else item.price
                    ) * line['quantity']

                    for line in lines

                    for item in [
                        items_by_id[line['item'].pk]
                    ]
                )

                # Coupon
                if order and order.coupon_id:
                    subtotal = max(
                        0,
                        subtotal - order.coupon.amount
                    )

                # Livraison
                store = StoreSettings.get_solo()

                shipping = (
                    0
                    if subtotal >= store.free_shipping_threshold
                    else store.shipping_fee
                )

                now = timezone.now()

                # Création / récupération de la commande
                placed_order = order

                if placed_order is None:
                    placed_order = Order(
                        user=(
                            request.user
                            if request.user.is_authenticated
                            else None
                        )
                    )

                placed_order.ref_code = (
                    placed_order.ref_code
                    or create_ref_code()
                )

                placed_order.idempotency_key = submission_key
                placed_order.ordered = True
                placed_order.ordered_date = now

                placed_order.customer_name = (
                    form.cleaned_data['full_name'].strip()
                )

                placed_order.phone_number = (
                    form.cleaned_data['phone_number']
                )

                placed_order.city = (
                    form.cleaned_data['city'].strip()
                )

                placed_order.delivery_address = (
                    form.cleaned_data['street_address'].strip()
                )

                # Aucun champ "notes" dans CheckoutForm
                placed_order.customer_notes = ''

                placed_order.subtotal = subtotal
                placed_order.shipping_cost = shipping
                placed_order.total_amount = subtotal + shipping
                placed_order.status = 'new'

                placed_order.save()

                # Produits de la commande
                for line in lines:

                    item = items_by_id[
                        line['item'].pk
                    ]

                    order_item = line['order_item']

                    if order_item:

                        order_item.quantity = line['quantity']

                        order_item.title_snapshot = item.title

                        order_item.unit_price_snapshot = (
                            item.discount_price
                            if item.discount_price is not None
                            else item.price
                        )

                        order_item.ordered = True

                        order_item.save()

                    else:

                        order_item = OrderItem.objects.create(
                            user=(
                                request.user
                                if request.user.is_authenticated
                                else None
                            ),
                            ordered=True,
                            item=item,
                            quantity=line['quantity'],
                            title_snapshot=item.title,
                            unit_price_snapshot=(
                                item.discount_price
                                if item.discount_price is not None
                                else item.price
                            ),
                        )

                        placed_order.items.add(order_item)

                    # Décrémentation du stock
                    updated = Item.objects.filter(
                        pk=item.pk,
                        is_active=True,
                        stock__gte=line['quantity'],
                    ).update(
                        stock=F('stock') - line['quantity']
                    )

                    if not updated:
                        raise StockUnavailable(
                            'Stock insuffisant pour ce produit. '
                            'Actualisez votre panier.'
                        )

                    item.stock -= line['quantity']

        except IntegrityError:

            placed_order = Order.objects.filter(
                idempotency_key=submission_key
            ).first()

            if placed_order is None:
                raise

            return redirect(
                'core:order-success',
                ref_code=placed_order.ref_code
            )

        except StockUnavailable as error:

            form.add_error(
                None,
                str(error)
            )

            return self.render_checkout(
                request,
                form,
                order,
                lines,
                status=409
            )

        # Nettoyage du panier
        request.session.pop('cart', None)

        request.session.pop(
            'checkout_submission_key',
            None
        )

        request.session[
            'last_checkout_submission_key'
        ] = submission_key

        messages.success(
            request,
            'Votre commande a été enregistrée avec succès.'
        )

        return redirect(
            'core:order-success',
            ref_code=placed_order.ref_code
        )


# def home(request):
#     context = {
#         'items': Item.objects.all()
#     }
#     return render(request, "index.html", context)
#
#
# def products(request):
#     context = {
#         'items': Item.objects.all()
#     }
#     return render(request, "product-detail.html", context)
#
#
# def shop(request):
#     context = {
#         'items': Item.objects.all()
#     }
#     return render(request, "shop.html", context)


def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    try:
        quantity = max(1, int(request.POST.get('quantity', request.GET.get('quantity', 1))))
    except (TypeError, ValueError):
        quantity = 1

    if not item.is_active or item.stock < 1:
        messages.error(request, 'Ce produit est épuisé.')
        return redirect('core:product', slug=slug)

    if not request.user.is_authenticated:
        cart = request.session.get('cart', {})
        if not isinstance(cart, dict):
            cart = {}
        current_quantity = int(cart.get(str(item.pk), 0))
        if current_quantity + quantity > item.stock:
            messages.error(request, 'Stock insuffisant pour cette quantité.')
            return redirect('core:product', slug=slug)
        cart[str(item.pk)] = current_quantity + quantity
        request.session['cart'] = cart
        messages.success(request, 'Produit ajouté au panier.')
        if request.POST.get('next') == 'checkout' or request.GET.get('next') == 'checkout':
            return redirect('core:checkout')
        return redirect('core:order-summary')

    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False).order_by('-pk')
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            if order_item.quantity + quantity > item.stock:
                messages.error(request, 'Stock insuffisant pour cette quantité.')
                return redirect('core:product', slug=slug)
            order_item.quantity += quantity
            order_item.save()
            messages.success(request, 'Quantité mise à jour.')
            return redirect('core:checkout' if request.POST.get('next') == 'checkout' else 'core:order-summary')
        else:
            order_item.quantity = quantity
            order_item.save()
            order.items.add(order_item)
            messages.success(request, 'Produit ajouté au panier.')
            return redirect('core:checkout' if request.POST.get('next') == 'checkout' else 'core:order-summary')
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        order_item.quantity = quantity
        order_item.save()
        order.items.add(order_item)
        messages.success(request, 'Produit ajouté au panier.')
    return redirect('core:checkout' if request.POST.get('next') == 'checkout' else 'core:order-summary')

def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    if not request.user.is_authenticated:
        cart = request.session.get('cart', {})
        cart.pop(str(item.pk), None)
        request.session['cart'] = cart
        return redirect('core:order-summary')
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            messages.info(request, "Item was removed from your cart.")
            return redirect("core:order-summary")
        else:
            # add a message saying the user dosent have an order
            messages.info(request, "Item was not in your cart.")
            return redirect("core:product", slug=slug)
    else:
        # add a message saying the user dosent have an order
        messages.info(request, "u don't have an active order.")
        return redirect("core:product", slug=slug)
    return redirect("core:product", slug=slug)


def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    if not request.user.is_authenticated:
        cart = request.session.get('cart', {})
        current_quantity = int(cart.get(str(item.pk), 0))
        if current_quantity > 1:
            cart[str(item.pk)] = current_quantity - 1
        else:
            cart.pop(str(item.pk), None)
        request.session['cart'] = cart
        return redirect('core:order-summary')
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, "This item qty was updated.")
            return redirect("core:order-summary")
        else:
            # add a message saying the user dosent have an order
            messages.info(request, "Item was not in your cart.")
            return redirect("core:product", slug=slug)
    else:
        # add a message saying the user dosent have an order
        messages.info(request, "u don't have an active order.")
        return redirect("core:product", slug=slug)
    return redirect("core:product", slug=slug)


def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, "This coupon does not exist")
        return redirect("core:checkout")


class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(
                    user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, "Successfully added coupon")
                return redirect("core:checkout")

            except ObjectDoesNotExist:
                messages.info(self.request, "You do not have an active order")
                return redirect("core:checkout")


class ContactView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'contact.html')

    def post(self, request, *args, **kwargs):
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        comment = request.POST.get('comment', '').strip()

        if not email:
            messages.error(
                request,
                "L'adresse e-mail est obligatoire."
            )
            return render(request, 'contact.html')

        if '@' not in email:
            messages.error(
                request,
                "Veuillez saisir une adresse e-mail valide."
            )
            return render(request, 'contact.html')

        ContactMessage.objects.create(
            name=name,
            email=email,
            phone=phone,
            comment=comment,
        )

        messages.success(
            request,
            "Votre message a bien été envoyé. Nous vous répondrons prochainement."
        )

        return redirect('core:contact')


class LegalPageView(View):
    def get(self, request, *args, **kwargs):
        slug = kwargs['slug']
        page = LegalPage.objects.filter(slug=slug, is_active=True).first()
        if page is None:
            fallback_pages = {
                'privacy': {
                    'title': 'Confidentialité',
                    'content': 'Les informations fournies lors d’une commande sont utilisées pour la traiter, organiser sa livraison et contacter le client à son sujet. Pour toute demande concernant ces informations, contactez la boutique.',
                },
                'refund': {
                    'title': 'Remboursement et retours',
                    'content': 'Pour toute demande concernant un article reçu, contactez la boutique en indiquant la référence de commande et le motif de votre demande. La boutique vous indiquera les modalités applicables.',
                },
                'terms': {
                    'title': 'Conditions d’utilisation',
                    'content': 'Les commandes sont enregistrées après validation du formulaire et restent soumises à la disponibilité des articles. Le paiement s’effectue à la livraison. Les informations détaillées de vente peuvent être complétées dans l’administration de la boutique.',
                },
                'delivery': {
                    'title': 'Livraison',
                    'content': 'Les frais de livraison et le seuil de gratuité sont affichés dans le récapitulatif avant confirmation. Les zones et délais applicables sont communiqués par la boutique lors de la confirmation de commande.',
                },
            }
            page = fallback_pages.get(slug)
            if page is None:
                from django.http import Http404
                raise Http404
        return render(request, 'legal_page.html', {'page': page})


class RequestRefundView(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {
            'form': form
        }
        return render(self.request, "request_refund.html", context)

    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')
            # edit the order
            try:
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested = True
                order.save()

                # store the refund
                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()

                messages.info(self.request, "Your request was received")
                return redirect("core:request-refund")

            except ObjectDoesNotExist:
                messages.info(self.request, "This order does not exist")
                return redirect("core:request-refund")
