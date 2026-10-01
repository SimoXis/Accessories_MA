from django.db.models import Sum

from .models import Order, StoreSettings


def storefront(request):
    if request.user.is_authenticated:
        cart_count = Order.objects.filter(
            user=request.user, ordered=False
        ).aggregate(total=Sum('items__quantity'))['total'] or 0
    else:
        cart = request.session.get('cart', {})
        cart_count = 0
        if isinstance(cart, dict):
            for quantity in cart.values():
                try:
                    cart_count += max(0, int(quantity))
                except (TypeError, ValueError):
                    continue
    return {
        'store_settings': StoreSettings.get_solo(),
        'cart_count': cart_count,
    }