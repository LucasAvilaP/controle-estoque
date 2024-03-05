# Generated by Django 5.0.1 on 2024-01-26 14:17

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestao_estoque', '0004_local_restaurante'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicolog',
            name='destino',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='log_destino', to='gestao_estoque.local'),
        ),
        migrations.AddField(
            model_name='historicolog',
            name='origem',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='log_origem', to='gestao_estoque.local'),
        ),
    ]
