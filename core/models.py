from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import Sum
from django.shortcuts import reverse
from django_countries.fields import CountryField


def validate_image_size(image):
    if image.size > 5 * 1024 * 1024:
        raise ValidationError('La taille maximale d’une image est de 5 Mo.')


IMAGE_VALIDATORS = [
    FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp']),
    validate_image_size,
]

# Create your models here.
CATEGORY_CHOICES = (
    ('SB', 'Shirts And Blouses'),
    ('TS', 'T-Shirts'),
    ('SK', 'Skirts'),
    ('HS', 'Hoodies&Sweatshirts')
)

LABEL_CHOICES = (
    ('S', 'sale'),
    ('N', 'new'),
    ('P', 'promotion')
)

ADDRESS_CHOICES = (
    ('B', 'Billing'),
    ('S', 'Shipping'),
)

ORDER_STATUS_CHOICES = (
    ('new', 'Nouvelle'),
    ('confirmed', 'Confirmée'),
    ('shipped', 'Expédiée'),
    ('delivered', 'Livrée'),
    ('cancelled', 'Annulée'),
    ('unreachable', 'Injoignable'),
)


class Slide(models.Model):
    caption1 = models.CharField(max_length=100)
    caption2 = models.CharField(max_length=100)
    link = models.CharField(max_length=100)
    image = models.ImageField(
        help_text="Size: 1920x570", validators=IMAGE_VALIDATORS)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return "{} - {}".format(self.caption1, self.caption2)


class StoreSettings(models.Model):
    store_name = models.CharField(max_length=100, default='ACCESORIES MA')
    announcement_text = models.CharField(
        max_length=180, default='LIVRAISON GRATUITE À PARTIR DE 370 DH')
    logo = models.ImageField(
        upload_to='store/', blank=True, validators=IMAGE_VALIDATORS)
    shipping_fee = models.FloatField(default=35)
    free_shipping_threshold = models.FloatField(default=370)
    cities = models.TextField(default=(
        'Casablanca\nRabat\nSalé\nMarrakech\nFès\nTanger\nAgadir\n'
        'Meknès\nOujda\nKénitra\nTétouan\nSafi\nEl Jadida\n'
        'Béni Mellal\nNador\nKhouribga\nSettat\nLaâyoune\nDakhla'
    ))
    phone_number = models.CharField(max_length=20, blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)
    instagram_url = models.URLField(blank=True)
    tiktok_url = models.URLField(blank=True)

    class Meta:
        verbose_name = 'Paramètres de la boutique'
        verbose_name_plural = 'Paramètres de la boutique'

    def __str__(self):
        return self.store_name

    @classmethod
    def get_solo(cls):
        return cls.objects.first() or cls()


class LegalPage(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=120)
    content = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title

class Category(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField()
    description = models.TextField()
    image = models.ImageField(validators=IMAGE_VALIDATORS)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("core:category", kwargs={
            'slug': self.slug
        })


class Item(models.Model):
    title = models.CharField(max_length=100)
    price = models.FloatField()
    discount_price = models.FloatField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    label = models.CharField(choices=LABEL_CHOICES, max_length=1)
    slug = models.SlugField()
    stock_no = models.CharField(max_length=10)
    description_short = models.CharField(max_length=50)
    description_long = models.TextField()
    image = models.ImageField(validators=IMAGE_VALIDATORS)
    is_active = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("core:product", kwargs={
            'slug': self.slug
        })

    def get_add_to_cart_url(self):
        return reverse("core:add-to-cart", kwargs={
            'slug': self.slug
        })

    def get_remove_from_cart_url(self):
        return reverse("core:remove-from-cart", kwargs={
            'slug': self.slug
        })


class ProductImage(models.Model):
    item = models.ForeignKey(
        Item, related_name='gallery_images', on_delete=models.CASCADE)
    image = models.ImageField(
        upload_to='products/gallery/', validators=IMAGE_VALIDATORS)
    alt_text = models.CharField(max_length=140, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'pk']

    def __str__(self):
        return self.alt_text or '{} image'.format(self.item.title)


class OrderItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, blank=True, null=True)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(
        Item, on_delete=models.SET_NULL, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    title_snapshot = models.CharField(max_length=100, blank=True)
    unit_price_snapshot = models.FloatField(blank=True, null=True)

    def __str__(self):
        title = self.title_snapshot or (
            self.item.title if self.item_id else 'Produit supprimé')
        return '{} x {}'.format(self.quantity, title)

    def get_total_item_price(self):
        price = self.unit_price_snapshot
        if price is None:
            price = self.item.price if self.item_id else 0
        return self.quantity * price

    def get_total_discount_item_price(self):
        if self.unit_price_snapshot is not None:
            return self.get_total_item_price()
        if not self.item_id or self.item.discount_price is None:
            return self.get_total_item_price()
        return self.quantity * self.item.discount_price

    def get_amount_saved(self):
        return self.get_total_item_price() - self.get_total_discount_item_price()

    def get_final_price(self):
        if self.unit_price_snapshot is not None:
            return self.get_total_item_price()
        if self.item_id and self.item.discount_price is not None:
            return self.get_total_discount_item_price()
        return self.get_total_item_price()


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, blank=True, null=True)
    ref_code = models.CharField(max_length=20)
    idempotency_key = models.CharField(
        max_length=64, blank=True, null=True, unique=True)
    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    ordered = models.BooleanField(default=False)
    shipping_address = models.ForeignKey(
        'BillingAddress', related_name='shipping_address', on_delete=models.SET_NULL, blank=True, null=True)
    billing_address = models.ForeignKey(
        'BillingAddress', related_name='billing_address', on_delete=models.SET_NULL, blank=True, null=True)
    payment = models.ForeignKey(
        'Payment', on_delete=models.SET_NULL, blank=True, null=True)
    coupon = models.ForeignKey(
        'Coupon', on_delete=models.SET_NULL, blank=True, null=True)
    being_delivered = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    refund_requested = models.BooleanField(default=False)
    refund_granted = models.BooleanField(default=False)
    customer_name = models.CharField(max_length=120, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100, blank=True)
    delivery_address = models.TextField(blank=True)
    customer_notes = models.TextField(blank=True)
    subtotal = models.FloatField(blank=True, null=True)
    shipping_cost = models.FloatField(blank=True, null=True)
    total_amount = models.FloatField(blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=ORDER_STATUS_CHOICES, default='new')
    internal_notes = models.TextField(blank=True)

    '''
    1. Item added to cart
    2. Adding a BillingAddress
    (Failed Checkout)
    3. Payment
    4. Being delivered
    5. Received
    6. Refunds
    '''

    def __str__(self):
        return self.user.username if self.user_id else self.ref_code

    def get_total(self):
        if self.total_amount is not None:
            return self.total_amount
        total = 0
        for order_item in self.items.all():
            total += order_item.get_final_price()
        if self.coupon:
            total -= self.coupon.amount
        return total


class BillingAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    street_address = models.CharField(max_length=100)
    apartment_address = models.CharField(max_length=100)
    country = CountryField(multiple=False)
    zip = models.CharField(max_length=100)
    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
    default = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name_plural = 'BillingAddresses'


class Payment(models.Model):
    stripe_charge_id = models.CharField(max_length=50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.SET_NULL, blank=True, null=True)
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class Coupon(models.Model):
    code = models.CharField(max_length=15)
    amount = models.FloatField()

    def __str__(self):
        return self.code


class Refund(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    reason = models.TextField()
    accepted = models.BooleanField(default=False)
    email = models.EmailField()

    def __str__(self):
        return f"{self.pk}"
class ContactMessage(models.Model):
    name = models.CharField(max_length=120, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Message de contact"
        verbose_name_plural = "Messages de contact"
        ordering = ["-created_at"]

    def __str__(self):
        return "{} - {}".format(self.name or "Sans nom", self.email)