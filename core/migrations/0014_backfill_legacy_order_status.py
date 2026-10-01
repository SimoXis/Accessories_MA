from django.db import migrations


def map_legacy_statuses(apps, schema_editor):
    Order = apps.get_model('core', 'Order')
    for order in Order.objects.all().iterator():
        if order.received:
            order.status = 'delivered'
        elif order.being_delivered:
            order.status = 'shipped'
        elif order.ordered:
            order.status = 'confirmed'
        else:
            order.status = 'new'
        order.save(update_fields=['status'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_auto_20260929_2329'),
    ]

    operations = [
        migrations.RunPython(map_legacy_statuses, migrations.RunPython.noop),
    ]