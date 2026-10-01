from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .models import Category, Item, Order, OrderItem, StoreSettings
from .admin import OrderAdmin


class ShopAndOrderFlowTests(TestCase):
    def setUp(self):
        category = Category.objects.create(
            title='Parfums Homme',
            slug='parfums-homme',
            description='Collection premium masculine',
            image=SimpleUploadedFile(
                'category.jpg',
                b'fake-image-content',
                content_type='image/jpeg'
            )
        )

        self.item_one = Item.objects.create(
            title='Amber Gold',
            price=199.00,
            discount_price=149.00,
            category=category,
            label='N',
            slug='amber-gold',
            stock_no='A-001',
            description_short='Parfum boisé intense',
            description_long='Une fragrance élégante et chaleureuse.',
            image=SimpleUploadedFile(
                'amber.jpg',
                b'fake-image-content',
                content_type='image/jpeg'
            )
        )

        self.item_two = Item.objects.create(
            title='Citrus Bloom',
            price=179.00,
            category=category,
            label='P',
            slug='citrus-bloom',
            stock_no='A-002',
            description_short='Éclat frais et lumineux',
            description_long='Un parfum frais parfait pour le quotidien.',
            image=SimpleUploadedFile(
                'citrus.jpg',
                b'fake-image-content',
                content_type='image/jpeg'
            )
        )

    def test_shop_search_filters_products(self):
        response = self.client.get(reverse('core:shop'), {'q': 'amber'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Amber Gold')
        self.assertNotContains(response, 'Citrus Bloom')
        self.assertIn('query', response.context)

    def test_order_success_page_exists(self):
        Order.objects.create(
            ref_code='ABC123',
            ordered_date=timezone.now(),
            ordered=True,
            customer_name='Client Test',
            phone_number='0612345678',
            city='Casablanca',
        )
        response = self.client.get(reverse('core:order-success', kwargs={'ref_code': 'ABC123'}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ABC123')
        self.assertContains(response, 'Client Test')

    def test_unknown_order_reference_returns_not_found(self):
        response = self.client.get(reverse('core:order-success', kwargs={'ref_code': 'UNKNOWN'}))

        self.assertEqual(response.status_code, 404)

    def test_guest_cod_checkout_uses_server_prices_and_stock(self):
        self.item_one.stock = 3
        self.item_one.save(update_fields=['stock'])
        StoreSettings.objects.create(shipping_fee=35, free_shipping_threshold=370)

        self.client.post(
            reverse('core:add-to-cart', kwargs={'slug': self.item_one.slug}),
            {'quantity': '2'},
        )
        checkout = self.client.get(reverse('core:checkout'))
        self.assertEqual(checkout.status_code, 200)
        submission_key = checkout.context['form']['submission_key'].value()
        payload = {
            'full_name': 'Client Test',
            'phone_number': '0612345678',
            'city': 'Casablanca',
            'street_address': '10 rue Exemple',
            'submission_key': submission_key,
        }

        response = self.client.post(reverse('core:checkout'), payload)
        order = Order.objects.get(idempotency_key=submission_key)

        self.assertRedirects(
            response, reverse('core:order-success', kwargs={'ref_code': order.ref_code}),
            fetch_redirect_response=False,
        )
        self.assertIsNone(order.user)
        self.assertEqual(order.subtotal, 298)
        self.assertEqual(order.shipping_cost, 35)
        self.assertEqual(order.total_amount, 333)
        self.assertEqual(self.item_one.__class__.objects.get(pk=self.item_one.pk).stock, 1)
        order_item = OrderItem.objects.get(order=order)
        self.assertEqual(order_item.title_snapshot, 'Amber Gold')
        self.assertEqual(order_item.unit_price_snapshot, 149)

        duplicate = self.client.post(reverse('core:checkout'), payload)
        self.assertEqual(Order.objects.count(), 1)
        self.assertRedirects(
            duplicate, reverse('core:order-success', kwargs={'ref_code': order.ref_code}),
            fetch_redirect_response=False,
        )

    def test_checkout_rejects_invalid_phone_without_creating_order(self):
        self.item_one.stock = 2
        self.item_one.save(update_fields=['stock'])
        self.client.post(
            reverse('core:add-to-cart', kwargs={'slug': self.item_one.slug}),
            {'quantity': '1'},
        )
        checkout = self.client.get(reverse('core:checkout'))
        payload = {
            'full_name': 'Client Test',
            'phone_number': '0812345678',
            'city': 'Casablanca',
            'street_address': '10 rue Exemple',
            'submission_key': checkout.context['form']['submission_key'].value(),
        }

        response = self.client.post(reverse('core:checkout'), payload)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(Item.objects.get(pk=self.item_one.pk).stock, 2)
        self.assertContains(response, 'numéro marocain valide', status_code=400)

    def test_storefront_pages_render_with_accessories_brand(self):
        self.item_one.stock = 2
        self.item_one.save(update_fields=['stock'])
        pages = [
            reverse('core:home'),
            reverse('core:shop'),
            reverse('core:product', kwargs={'slug': self.item_one.slug}),
            reverse('core:category', kwargs={'slug': self.item_one.category.slug}),
            reverse('core:contact'),
            reverse('core:legal', kwargs={'slug': 'delivery'}),
        ]
        for page in pages:
            with self.subTest(page=page):
                response = self.client.get(page)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'ACCESORIES MA')

    def test_free_delivery_threshold_is_applied(self):
        self.item_two.stock = 3
        self.item_two.save(update_fields=['stock'])
        StoreSettings.objects.create(shipping_fee=35, free_shipping_threshold=370)
        self.client.post(
            reverse('core:add-to-cart', kwargs={'slug': self.item_two.slug}),
            {'quantity': '3'},
        )
        checkout = self.client.get(reverse('core:checkout'))
        payload = {
            'full_name': 'Client Test',
            'phone_number': '0712345678',
            'city': 'Rabat',
            'street_address': '20 avenue Exemple',
            'submission_key': checkout.context['form']['submission_key'].value(),
        }

        self.client.post(reverse('core:checkout'), payload)
        order = Order.objects.get()

        self.assertEqual(order.subtotal, 537)
        self.assertEqual(order.shipping_cost, 0)
        self.assertEqual(order.total_amount, 537)

    def test_checkout_rechecks_stock_before_order_creation(self):
        self.item_one.stock = 2
        self.item_one.save(update_fields=['stock'])
        self.client.post(
            reverse('core:add-to-cart', kwargs={'slug': self.item_one.slug}),
            {'quantity': '2'},
        )
        checkout = self.client.get(reverse('core:checkout'))
        payload = {
            'full_name': 'Client Test',
            'phone_number': '0612345678',
            'city': 'Casablanca',
            'street_address': '10 rue Exemple',
            'submission_key': checkout.context['form']['submission_key'].value(),
        }
        Item.objects.filter(pk=self.item_one.pk).update(stock=1)

        response = self.client.post(reverse('core:checkout'), payload)

        self.assertEqual(response.status_code, 409)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(Item.objects.get(pk=self.item_one.pk).stock, 1)

    def test_cancelling_order_restores_stock_in_admin(self):
        self.item_one.stock = 0
        self.item_one.save(update_fields=['stock'])
        order = Order.objects.create(
            ref_code='CANCEL123',
            ordered_date=timezone.now(),
            ordered=True,
            status='new',
        )
        order_item = OrderItem.objects.create(
            item=self.item_one,
            quantity=2,
            ordered=True,
            title_snapshot=self.item_one.title,
            unit_price_snapshot=149,
        )
        order.items.add(order_item)
        request = RequestFactory().post('/admin/')

        order.status = 'cancelled'
        OrderAdmin(Order, AdminSite()).save_model(request, order, None, True)

        self.assertEqual(Item.objects.get(pk=self.item_one.pk).stock, 2)
