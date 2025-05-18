from django.db import models
from django.utils.translation import gettext as _
from core.models import City, Region, District, Town, Neighborhood
import datetime
from dateutil.relativedelta import relativedelta  
from django.contrib.auth import get_user_model

User = get_user_model()
import logging
logger = logging.getLogger(__name__)

# Create your models here.
Type_Choices = [
    ('revenues' , 'Revenues'),
    ('expenses' , 'Expenses'),
]

#Items
class Item(models.Model):
    name = models.CharField(max_length=255,verbose_name=_('Item Name'))
    type_choice = models.CharField(max_length =255 ,choices=Type_Choices , verbose_name=_('Type'))

    def __str__(self):
        return self.name

#Contracts
class Contract(models.Model):
    PAYMENT_FREQUENCY_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
    ]
    # Relations to geographical entities
    city = models.ForeignKey(City, null=True, blank=True, related_name='contracts', on_delete=models.CASCADE)
    region = models.ForeignKey(Region, null=True, blank=True, related_name='contracts', on_delete=models.CASCADE)
    districts = models.ManyToManyField(District, blank=True, related_name='contracts')
    towns = models.ManyToManyField(Town, blank=True, related_name='contracts')  
    neighborhoods = models.ManyToManyField(Neighborhood, blank=True, related_name='contracts')

    # Contract details
    provider_name = models.CharField(max_length=255, verbose_name=_('Provider Name'), null=True, blank=True) 
    duration = models.PositiveIntegerField(default=12, verbose_name=_('Duration (Months)'), help_text=_('Contract duration in months (1-120)'))  
    entry_date = models.DateField(auto_now_add=True, null=True, blank=True, verbose_name=_("Entry Date"))
    contract_date = models.DateField(default=datetime.date.today, verbose_name=_("Contract Date"))                  
    commencing_date = models.DateField(null=True, blank=True, verbose_name=_("Commencing Date"))
    end_date = models.DateField(verbose_name=_("End Date"), blank=True, null=True)    
    value = models.IntegerField(verbose_name=_('Value (EGP)'))  
    remaining = models.IntegerField(verbose_name=_('Remaining Amount'), null=True, blank=True)
    created_by = models.ForeignKey(User, null=True, blank=True, related_name="contract_created", on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, null=True, blank=True, related_name="contract_updated", on_delete=models.SET_NULL)
    updated_at = models.DateTimeField(auto_now=True)
    down_payment_percentage = models.FloatField(
    null=True, blank=True, verbose_name=_("Down Payment (%)"),
    help_text=_("If set, the value field will be calculated")
    )
    down_payment_value = models.IntegerField(
        null=True, blank=True, verbose_name=_("Down Payment (EGP)"),
        help_text=_("If set, it overrides percentage")
    )
    payment_frequency = models.CharField(
        max_length=10,
        choices=PAYMENT_FREQUENCY_CHOICES,
        default='monthly',
        verbose_name=_("Payment Frequency")
    )
    
    def __str__(self):
        return f"Contract with {self.provider_name}"    

    def save(self, *args, **kwargs):
        # Calculate down_payment_value if only percentage is provided
        if self.down_payment_percentage is not None and self.down_payment_value is None:
            self.down_payment_value = int((self.down_payment_percentage / 100) * self.value)

        # Calculate down_payment_percentage if only value is provided
        elif self.down_payment_value is not None and self.down_payment_percentage is None:
            self.down_payment_percentage = round((self.down_payment_value / self.value) * 100, 2)

        # Fallback if neither is provided
        elif self.down_payment_value is None and self.down_payment_percentage is None:
            self.down_payment_value = 0
            self.down_payment_percentage = 0

        # Ensure remaining is value minus down payment
        self.remaining = self.value - (self.down_payment_value or 0)
        
        if self.commencing_date and self.duration:
            self.end_date = self.commencing_date + relativedelta(months=self.duration)
        
        user = kwargs.pop('user', None)

        if not self.pk:  # If creating
            if user:
                self.created_by = user
        else:  # If updating
            if user:
                self.updated_by = user
                
        super().save(*args, **kwargs)
        self.generate_expected_payments()

        self.commit_contract_to_related_entities()
    
    def generate_expected_payments(self):
        from datetime import timedelta

        # Clear old payments
        self.expected_payments.all().delete()

        remaining_amount = self.remaining
        frequency_months = 1 if self.payment_frequency == 'monthly' else 3
        number_of_payments = self.duration // frequency_months

        payment_value = remaining_amount / number_of_payments
        start_date = self.contract_date + relativedelta(months=1)

        for i in range(number_of_payments):
            payment_date = start_date + relativedelta(months=i * frequency_months)
            ExpectedPayment.objects.create(
                contract=self,
                payment_date=payment_date,
                amount=round(payment_value)
            )
    def commit_contract_to_related_entities(self):
        """Commit this contract based on the hierarchy selection logic."""
        if self.city:
            self._commit_to_city(self.city)

        if self.region:
            region_districts = list(self.districts.all()) 
            self._commit_to_region(self.region, region_districts)

        for district in self.districts.all():
            district_towns = list(self.towns.filter(district=district))
            self._commit_to_district(district, district_towns)

        for town in self.towns.all():
            town_neighborhoods = list(self.neighborhoods.filter(town=town))
            self._commit_to_town(town, town_neighborhoods)

    def _commit_to_city(self, city):
        """Commit all regions (and below) under the given city."""
        for region in city.regions.all():
            self._commit_to_region(region, [])

    def _commit_to_region(self, region, selected_districts):
        """Commit selected or all districts in a region."""
        all_districts = region.districts.all()
        districts_to_commit = selected_districts or all_districts
        for district in districts_to_commit:
            district_towns = list(self.towns.filter(district=district))
            self._commit_to_district(district, district_towns)

    def _commit_to_district(self, district, selected_towns):
        """Commit selected or all towns in a district."""
        all_towns = district.towns.all()
        towns_to_commit = selected_towns or all_towns
        for town in towns_to_commit:
            town_neighborhoods = list(self.neighborhoods.filter(town=town))
            self._commit_to_town(town, town_neighborhoods)

    def _commit_to_town(self, town, selected_neighborhoods):
        """Commit selected or all neighborhoods in a town."""
        all_neighborhoods = town.neighborhoods.all()
        neighborhoods_to_commit = selected_neighborhoods or all_neighborhoods
        for neighborhood in neighborhoods_to_commit:
            self._commit_to_selected_neighborhoods([neighborhood])

    def _commit_to_selected_neighborhoods(self, selected_neighborhoods):
        """Final commit to neighborhoods — where custom logic can be applied."""
        for neighborhood in selected_neighborhoods:
            # Example: Assign contract ID to neighborhood, create log, or link to M2M
            pass
        
class ExpectedPayment(models.Model):
    contract = models.ForeignKey(
        Contract, related_name='expected_payments', on_delete=models.CASCADE
    )
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Payment of {self.amount} on {self.payment_date}"

# Expense Model
class Expense(models.Model):
    city = models.ForeignKey(City, null=True, blank=True, related_name='expenses', on_delete=models.CASCADE)
    regions = models.ManyToManyField(Region, blank=True, related_name='expenses')
    districts = models.ManyToManyField(District, blank=True, related_name='expenses')
    towns = models.ManyToManyField(Town, blank=True, related_name='expenses')
    neighborhoods = models.ManyToManyField(Neighborhood, blank=True, related_name='expenses')
    
    receipt_number = models.CharField(max_length=50, null=True)
    receipt_file = models.FileField(upload_to='expenses/receipts/', null=True, blank=True)
    receipt_date = models.DateField(null=True, blank=True)

    register_number = models.CharField(max_length=15, unique=True, blank=True)
    created_by = models.ForeignKey(User, null=True, blank=True, related_name="expense_created", on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, null=True, blank=True, related_name="expense_updated", on_delete=models.SET_NULL)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.register_number

    @property
    def total_expenses(self):
        return self.expense_items.aggregate(total=models.Sum('value'))['total'] or 0

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)

        if not self.pk:
            if user:
                self.created_by = user
        else:
            if user:
                self.updated_by = user

        creating = not self.pk
        if creating and not self.register_number:
            super().save(*args, **kwargs)  # Save to get ID
            self.register_number = f"E{self.id}"
            super().save(update_fields=["register_number"])
        else:
            super().save(*args, **kwargs)

        self.commit_selected_entities()

    def commit_selected_entities(self):
        """
        Automatically associate districts, towns, and neighborhoods
        based on selected regions and manual selections.
        """
        if self.city:
            self._commit_to_city(self.city)

        for region in self.regions.all():
            self._commit_to_region(region, list(self.districts.filter(region=region)))

        for district in self.districts.all():
            self._commit_to_district(district, list(self.towns.filter(district=district)))

        for town in self.towns.all():
            self._commit_to_town(town, list(self.neighborhoods.filter(town=town)))

    def _commit_to_city(self, city):
        for region in city.regions.all():
            self._commit_to_region(region, list(self.districts.filter(region=region)))

    def _commit_to_region(self, region, selected_districts):
        districts = selected_districts or region.districts.all()
        for district in districts:
            towns = list(self.towns.filter(district=district))
            self._commit_to_district(district, towns)

    def _commit_to_district(self, district, selected_towns):
        towns = selected_towns or district.towns.all()
        for town in towns:
            neighborhoods = list(self.neighborhoods.filter(town=town))
            self._commit_to_town(town, neighborhoods)

    def _commit_to_town(self, town, selected_neighborhoods):
        neighborhoods = selected_neighborhoods or town.neighborhoods.all()
        # Reserved for future logic
        pass


# ExpenseItem Model
class ExpenseItem(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='expense_items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    contract = models.ForeignKey(Contract, null=True, blank=True, on_delete=models.CASCADE)

    value = models.IntegerField()
    taxes = models.IntegerField(default=0)
    hanged_value = models.IntegerField(default=0)
    amount_due = models.IntegerField(default=0)
    paid_for = models.CharField(max_length=255, null=True, blank=True)
    on_date = models.DateField()
    other_text = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.expense.register_number} - {self.item.name} - EGP{self.value}"

    def save(self, *args, **kwargs):
        
        # If item is contracting and a contract is set, pull location info from contract
        if self.item and self.item.type_choice == 'expenses' and self.contract:
            contract = self.contract
            expense = self.expense
            if contract.city:
                expense.city = contract.city
            if contract.region:
                expense.region = contract.region
            expense.districts.set(contract.districts.all())
            expense.towns.set(contract.towns.all())
            expense.neighborhoods.set(contract.neighborhoods.all())
            expense.save()

        super().save(*args, **kwargs)
        # 🔥 Update Contract Remaining if linked
        if self.contract:
            total_amount_due = ExpenseItem.objects.filter(contract=self.contract).aggregate(total=models.Sum('amount_due'))['total'] or 0
            self.contract.remaining = self.contract.value - total_amount_due
            self.contract.save()

# Revenues
class Revenue(models.Model):
    city = models.ForeignKey(City, null=True, blank=True, related_name='revenues', on_delete=models.CASCADE)
    region = models.ManyToManyField(Region, blank=True, related_name='revenues')

    receipt_number = models.CharField(max_length=50, null=True, blank=True)
    receipt_file = models.FileField(upload_to='revenues/receipts/', null=True, blank=True)
    receipt_date = models.DateField(null=True, blank=True)
    
    register_number = models.CharField(max_length=15 , unique=True, blank=True)
    created_by = models.ForeignKey(User, null=True, blank=True, related_name="revenue_created", on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, null=True, blank=True, related_name="revenue_updated", on_delete=models.SET_NULL)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.register_number
    
    @property
    def total_revenues(self):
        return self.revenue_items.aggregate(total=models.Sum('value'))['total'] or 0    

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        
        if not self.pk and user:
            self.created_by = user
        elif user:
            self.updated_by = user
                
        creating = not self.pk
        if creating and not self.register_number:
            super().save(*args, **kwargs) 
            self.register_number = f"E{self.id}"
            super().save(update_fields=["register_number"])
        else:
            super().save(*args, **kwargs)

# RevenueItem Model
class RevenueItem(models.Model):
    revenue = models.ForeignKey(Revenue ,on_delete=models.CASCADE ,null = True, blank=True ,related_name='revenue_items')
    item = models.ForeignKey(Item ,on_delete=models.CASCADE ,null=True)
    value = models.IntegerField()
    from_date = models.DateField()
    to_date = models.DateField()
    other_text = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f'{self.revenue.register_number} - {self.item.name} - EGP{self.value}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
 
