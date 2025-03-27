import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from hygienebox.models import ExpenseItem


@receiver(post_save, sender=ExpenseItem)
def decrease_remaining_amount_contract(sender, instance, **kwargs):
    """Decrease remaining amount when a new expense is added."""
    if instance.contract:
        contract = instance.contract
        contract.remaining = max(0, contract.remaining - instance.value)  # Prevent negative values
        contract.save()

@receiver(post_delete, sender=ExpenseItem)
def increase_remaining_amount_contract(sender, instance, **kwargs):
    """Increase remaining amount when an expense is deleted."""
    if instance.contract:
        contract = instance.contract
        contract.remaining += instance.value  # Add back the deleted value
        contract.save()
