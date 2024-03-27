# Generated by Django 5.0.1 on 2024-03-26 14:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gestao_estoque', '0019_transacoe_motivo'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='transacoe',
            options={'permissions': (('can_approve_transaction', 'Pode aprovar transação'), ('can_reject_transaction', 'Pode rejeitar transação'), ('can_update', 'Pode atualizar'), ('can_register_loss', 'Pode registrar perda'), ('can_loan', 'Pode realizar empréstimo'), ('can_return', 'Pode realizar devolução'))},
        ),
    ]
