# Generated by Django 5.0.1 on 2024-02-21 17:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produtos', '0005_produto_apelido'),
    ]

    operations = [
        migrations.AddField(
            model_name='estoqueproduto',
            name='apelido',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
