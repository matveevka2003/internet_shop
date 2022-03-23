# Generated by Django 4.0.2 on 2022-03-15 09:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_remove_order_customer'),
        ('users', '0014_user_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='orders.order'),
        ),
    ]
