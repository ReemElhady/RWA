from django.db import models
from core.models import Area , Neighborhood
from simple_history.models import HistoricalRecords
from django.utils.translation import gettext as _
from django.dispatch import receiver
from django.db.models.signals import post_save , post_delete

import logging
logger = logging.getLogger(__name__)

# Create your models here.
Type_Choices = [
    ('revenues' , 'Revenues'),
    ('expenses' , 'Expenses'),
]


class RevenueReg(models.Model):
    register_number = models.CharField(max_length=15 , unique=True, blank=True)
    site = models.ForeignKey(Area , on_delete=models.CASCADE)
    neighborhood = models.ForeignKey(Neighborhood , on_delete=models.CASCADE , null=True , blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.register_number
    
    @property
    def total_revenues(self):
        """Calculate total revenue from related items"""
        return self.revenue_items.aggregate(total=models.Sum('value'))['total'] or 0    
    
    def save(self, *args, **kwargs):
        # Check if it's a new object (no PK yet) and save the first time
        if not self.pk:
            super().save(*args, **kwargs)
            # Generate the register number only on the first save
            if not self.register_number:
                self.register_number = f'R{self.id}'
                # Save again to update the register_number after ID is generated
                super().save(*args, **kwargs)
    
        # Allow neighborhood to be cleared and updated properly
        if self.neighborhood == '':
            self.neighborhood = None

        # Always save for updates and modifications
        super().save(*args, **kwargs)

class ExpenseReg(models.Model):
    register_number = models.CharField(max_length=15 , unique=True, blank=True)
    site = models.ForeignKey(Area , on_delete=models.CASCADE)
    neighborhood = models.ForeignKey(Neighborhood , on_delete=models.CASCADE , null=True , blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.register_number
    
    @property
    def total_expenses(self):
        """Calculate total expenses from related items"""
        return self.expense_items.aggregate(total=models.Sum('value'))['total'] or 0    
    
    def save(self, *args, **kwargs):
        # Save first to get an ID
        if not self.pk:
            super().save(*args, **kwargs)
            # Generate register_number only if it's still empty
            if not self.register_number:
                self.register_number = f'E{self.id}'
                # Save again to update the register_number
                super().save(*args, **kwargs)
        # Allow neighborhood to be cleared and updated properly
        if self.neighborhood == '':
            self.neighborhood = None

        # Always save for updates and modifications
        super().save(*args, **kwargs)

class Item(models.Model):
    name = models.CharField(max_length=255,verbose_name=_('Item Name'))
    type_choice = models.CharField(max_length =255 ,choices=Type_Choices , verbose_name=_('Type'))

    def __str__(self):
        return self.name

class RevenueItem(models.Model):
    revenue = models.ForeignKey(RevenueReg , on_delete=models.CASCADE , null = True, blank=True , related_name='revenue_items')
    item = models.ForeignKey(Item , on_delete=models.CASCADE ,null=True)
    value = models.IntegerField()
    other_title = models.CharField(max_length=255,null=True, blank=True)
    from_date = models.DateField()
    to_date = models.DateField()
    history = HistoricalRecords(user_related_name="historical_revenue_items")

    def __str__(self):
        return f'{self.revenue.register_number} - {self.item.name} - EGP{self.value}'

class ServiceProvider(models.Model):
    name = models.CharField(max_length=255, verbose_name=_('Name'))
    def __str__(self):
        return self.name

class Contract(models.Model):
    site = models.ForeignKey(Area , on_delete=models.CASCADE ,verbose_name=_('Area'))
    neighborhood = models.ForeignKey(Neighborhood , on_delete=models.CASCADE , null=True , blank=True,verbose_name=_('Neighborhood'))
    service_provider = models.ForeignKey(ServiceProvider , on_delete=models.CASCADE,verbose_name=_('Service Provider'))
    value = models.IntegerField(verbose_name=_('Value (EGP)'))
    from_date = models.DateField(verbose_name=_('from'))
    to_date = models.DateField(verbose_name=_('to'))
    remaining = models.IntegerField(verbose_name=_('Remaining Amount'),null=True,blank=True)
    def __str__(self):
        return self.service_provider.name
    def save(self, *args, **kwargs):
        """Initialize remaining amount to the contract value on creation."""
        if self.remaining is None:
            self.remaining = self.value
        super().save(*args, **kwargs)

class ExpenseItem(models.Model):
    expense = models.ForeignKey(ExpenseReg , on_delete=models.CASCADE, null = True, blank=True, related_name='expense_items')
    item = models.ForeignKey(Item , on_delete=models.CASCADE ,null=True)
    value = models.IntegerField()
    other_title = models.CharField(max_length=255,null=True, blank=True)
    from_date = models.DateField()
    history = HistoricalRecords(user_related_name="historical_expense_items")
    contract = models.ForeignKey(Contract , on_delete=models.CASCADE , null=True  , blank =True)
    def __str__(self):
        return f'{self.expense.register_number} - {self.item.name} - EGP{self.value}'