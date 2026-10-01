from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse
from django.utils.html import format_html
import csv
import re
from urllib.parse import quote

from .models import Item, ProductImage, OrderItem, Order, Payment, Coupon, Refund, BillingAddress, Category, Slide, StoreSettings, LegalPage,ContactMessage


# Register your models here.


def make_refund_accepted(modeladmin, request, queryset):
    queryset.update(refund_requested=False, refund_granted=True)


make_refund_accepted.short_description = 'Update orders to refund granted'


class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'ref_code', 'ordered_date', 'customer_name', 'phone_number',
        'city', 'total_amount', 'status', 'customer_actions', 'ordered'
    ]
    list_display_links = ['ref_code']
    list_editable = ['status']
    list_filter = ['status', 'ordered_date', 'city', 'ordered']
    search_fields = [
        'user__username', 'ref_code', 'customer_name', 'phone_number', 'city'
    ]
    actions = [make_refund_accepted, 'export_orders_csv']

    def customer_actions(self, obj):
        if not obj.phone_number:
            return '-'
        digits = re.sub(r'\D', '', obj.phone_number)
        whatsapp_number = '212' + digits[1:] if digits.startswith('0') else digits
        message = quote(
            'Bonjour, nous vous contactons concernant votre commande n°{} chez ACCESORIES MA.'.format(obj.ref_code)
        )
        return format_html(
            '<a href="tel:{0}">Appeler</a> · <a href="https://wa.me/{1}?text={2}" target="_blank" rel="noopener">WhatsApp</a>',
            obj.phone_number,
            whatsapp_number,
            message,
        )

    customer_actions.short_description = 'Actions client'

    def save_model(self, request, obj, form, change):
        if not change:
            return super().save_model(request, obj, form, change)
        previous_status = Order.objects.get(pk=obj.pk).status
        if previous_status == obj.status:
            return super().save_model(request, obj, form, change)

        with transaction.atomic():
            order_items = obj.items.select_related('item').all()
            if obj.status == 'cancelled' and previous_status != 'cancelled':
                for order_item in order_items:
                    if order_item.item_id:
                        order_item.item.stock = F('stock') + order_item.quantity
                        order_item.item.save(update_fields=['stock'])
            elif previous_status == 'cancelled' and obj.status != 'cancelled':
                for order_item in order_items:
                    if not order_item.item_id:
                        raise ValidationError(
                            'Impossible de réactiver une commande contenant un produit supprimé.')
                    updated = Item.objects.filter(
                        pk=order_item.item_id,
                        is_active=True,
                        stock__gte=order_item.quantity,
                    ).update(stock=F('stock') - order_item.quantity)
                    if not updated:
                        raise ValidationError(
                            'Stock insuffisant pour réactiver cette commande.')
            super().save_model(request, obj, form, change)

    def export_orders_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="orders.csv"'
        response.write('\ufeff')
        writer = csv.writer(response)
        writer.writerow([
            'Référence', 'Date', 'Client', 'Téléphone', 'Adresse', 'Ville',
            'Produits', 'Sous-total', 'Livraison', 'Total', 'Statut'
        ])
        for order in queryset.prefetch_related('items__item'):
            items = '; '.join(
                '{} x {}'.format(
                    order_item.title_snapshot or (
                        order_item.item.title if order_item.item_id else 'Produit supprimé'),
                    order_item.quantity,
                ) for order_item in order.items.all()
            )
            values = [
                order.ref_code,
                order.ordered_date,
                order.customer_name,
                order.phone_number,
                order.delivery_address,
                order.city,
                items,
                order.subtotal,
                order.shipping_cost,
                order.total_amount,
                order.get_status_display(),
            ]
            writer.writerow([
                "'" + str(value) if str(value).startswith(('=', '+', '-', '@')) else value
                for value in values
            ])
        return response

    export_orders_csv.short_description = 'Exporter les commandes en CSV'


class AddressAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'street_address',
        'apartment_address',
        'country',
        'zip',
        'address_type',
        'default'
    ]
    list_filter = ['default', 'address_type', 'country']
    search_fields = ['user', 'street_address', 'apartment_address', 'zip']


def copy_items(modeladmin, request, queryset):
    for object in queryset:
        object.id = None
        object.save()


copy_items.short_description = 'Copy Items'


class ItemAdmin(admin.ModelAdmin):
    class ProductImageInline(admin.TabularInline):
        model = ProductImage
        extra = 1

    list_display = [
        'title', 'category', 'price', 'discount_price', 'stock', 'is_active'
    ]
    list_filter = ['category', 'is_active']
    list_editable = ['stock', 'is_active']
    search_fields = ['title', 'category__title', 'stock_no']
    prepopulated_fields = {"slug": ("title",)}
    actions = [copy_items]
    inlines = [ProductImageInline]

class CategoryAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'is_active'
    ]
    list_filter = ['title', 'is_active']
    search_fields = ['title', 'is_active']
    prepopulated_fields = {"slug": ("title",)}


admin.site.register(Item, ItemAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Slide)
admin.site.register(OrderItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(Payment)
admin.site.register(Coupon)
admin.site.register(Refund)
admin.site.register(BillingAddress, AddressAdmin)


@admin.register(StoreSettings)
class StoreSettingsAdmin(admin.ModelAdmin):
    list_display = ['store_name', 'shipping_fee', 'free_shipping_threshold']

    def has_add_permission(self, request):
        return not StoreSettings.objects.exists() and super().has_add_permission(request)


@admin.register(LegalPage)
class LegalPageAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'is_active']
    list_editable = ['is_active']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title', 'content']

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'email',
        'phone',
        'created_at',
    ]

    search_fields = [
        'name',
        'email',
        'phone',
        'comment',
    ]

    list_filter = [
        'created_at',
    ]

    readonly_fields = [
        'created_at',
    ]

    ordering = [
        '-created_at',
    ]