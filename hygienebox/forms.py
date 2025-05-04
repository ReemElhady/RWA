from .models import Contract, Expense, ExpenseItem, Item, Revenue, RevenueItem
from django import forms
from django.forms import inlineformset_factory
from core.models import City, Region, District, Town, Neighborhood
from django.utils.translation import gettext_lazy as _

#Contracts
class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = [
            'provider_name', 'value', 'remaining', 'duration',
            'contract_date', 'commencing_date', 'end_date',
            'city', 'region', 'districts', 'towns', 'neighborhoods'
        ]
        labels = {
            'provider_name': _("Provider Name"),
            'value': _("Value"),
            'remaining': _("Remaining"),
            'duration': _("Duration"),
            'contract_date': _("Contract Date"),
            'commencing_date': _("Commencing Date"),
            'end_date': _("End Date"),
            'city': _("City"),
            'region': _("Region"),
            'districts': _("Districts"),
            'towns': _("Towns"),
            'neighborhoods': _("Neighborhoods"),
        }
        widgets = {
            'contract_date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'commencing_date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'provider_name': forms.TextInput(attrs={'class': 'input'}),
            'value': forms.NumberInput(attrs={'class': 'input'}),
            'duration': forms.NumberInput(attrs={'class': 'input'}),
            'remaining': forms.NumberInput(attrs={'class': 'input'}),
            'city': forms.Select(attrs={'class': 'select is-fullwidth'}),
            'region': forms.Select(attrs={'class': 'select is-fullwidth'}),
            'districts': forms.SelectMultiple(attrs={'class': 'select is-multiple is-fullwidth'}),
            'towns': forms.SelectMultiple(attrs={'class': 'select is-multiple is-fullwidth'}),
            'neighborhoods': forms.SelectMultiple(attrs={'class': 'select is-multiple is-fullwidth'}),
        }
        
#Expenses     
class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['city', 'region', 'districts', 'towns', 'neighborhoods']
        labels = {
            'city': _("City"),
            'region': _("Region"),
            'districts': _("Districts"),
            'towns': _("Towns"),
            'neighborhoods': _("Neighborhoods"),
        }
        widgets = {
            'city': forms.Select(attrs={'class': 'select is-fullwidth'}),
            'region': forms.Select(attrs={'class': 'select is-fullwidth'}),
            'districts': forms.SelectMultiple(attrs={'class': 'select is-multiple is-fullwidth'}),
            'towns': forms.SelectMultiple(attrs={'class': 'select is-multiple is-fullwidth'}),
            'neighborhoods': forms.SelectMultiple(attrs={'class': 'select is-multiple is-fullwidth'}),
        }

class ExpenseItemForm(forms.ModelForm):
    class Meta:
        model = ExpenseItem
        fields = ['item', 'contract', 'value', 'taxes', 'hanged_value', 'amount_due', 'on_date', 'receipt_number', 'receipt_file', 'other_text']
        labels = {
            'item': _("Item"),
            'contract': _("Contract"),
            'value': _("Value"),
            'taxes': _("Taxes"),
            'hanged_value': _("Hanged Value"),
            'amount_due': _("Amount Due"),
            'on_date': _("On Date"),
            'receipt_number': _("Receipt Number"),
            'receipt_file': _("Receipt File"),
            'other_text': _("Other Description"),
        }
        widgets = {
            'item': forms.Select(attrs={'class': 'input'}),
            'contract': forms.Select(attrs={'class': 'input'}),
            'value': forms.NumberInput(attrs={'class': 'input'}),
            'taxes': forms.NumberInput(attrs={'class': 'input'}),
            'hanged_value': forms.NumberInput(attrs={'class': 'input'}),
            'amount_due': forms.NumberInput(attrs={'class': 'input'}),
            'on_date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'receipt_number': forms.TextInput(attrs={'class': 'input'}),
            'receipt_file': forms.FileInput(attrs={'class': 'input'}),
            'other_text': forms.TextInput(attrs={'class': 'input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter item queryset
        self.fields['item'].queryset = Item.objects.filter(type_choice='expenses')

        # Now control fields based on instance data
        instance = kwargs.get('instance')
        if instance and instance.pk:
            if instance.item:
                if instance.contract:
                    if 'other_text' in self.fields:
                        self.fields['other_text'].widget = forms.HiddenInput()
                        self.fields['other_text'].required = False
                elif instance.item.name.strip() == 'أخري':
                    # It's an "Other" item
                    for field_name in ['taxes', 'hanged_value', 'amount_due', 'contract']:
                        if field_name in self.fields:
                            self.fields[field_name].required = False
                            self.fields[field_name].widget = forms.HiddenInput()
                else:
                    # Regular item
                    for field_name in ['taxes', 'hanged_value', 'amount_due', 'other_text', 'contract']:
                        if field_name in self.fields:
                            self.fields[field_name].required = False
                            self.fields[field_name].widget = forms.HiddenInput()
            else:
                # No item at all
                for field_name in ['taxes', 'hanged_value', 'amount_due', 'other_text', 'contract']:
                    if field_name in self.fields:
                        self.fields[field_name].required = False
                        self.fields[field_name].widget = forms.HiddenInput()

ExpenseItemFormSet = inlineformset_factory(
    Expense, ExpenseItem,
    form=ExpenseItemForm,
    fields='__all__',
    extra=0,
    can_delete=True
)

#Revenues
class RevenueForm(forms.ModelForm):
    class Meta:
        model = Revenue
        fields = ['city', 'region', 'districts', 'towns', 'neighborhoods']
        labels = {
            'city': _("City"),
            'region': _("Region"),
            'districts': _("Districts"),
            'towns': _("Towns"),
            'neighborhoods': _("Neighborhoods"),
        }
        widgets = {
            'city': forms.Select(attrs={'class': 'select is-fullwidth'}),
            'region': forms.Select(attrs={'class': 'select is-fullwidth'}),
            'districts': forms.SelectMultiple(attrs={'class': 'select is-multiple is-fullwidth'}),
            'towns': forms.SelectMultiple(attrs={'class': 'select is-multiple is-fullwidth'}),
            'neighborhoods': forms.SelectMultiple(attrs={'class': 'select is-multiple is-fullwidth'}),
        }
        
class RevenueItemForm(forms.ModelForm):
    class Meta:
        model = RevenueItem
        fields = ['item', 'value', 'from_date', 'to_date', 'receipt_number', 'receipt_file', 'other_text']
        labels = {
            'item': _("Item"),
            'value': _("Value"),
            'from_date': _("From Date"),
            'to_date': _("To Date"),
            'receipt_number': _("Receipt Number"),
            'receipt_file': _("Receipt File"),
            'other_text': _("Other Description"),
        }
        widgets = {
            'item': forms.Select(attrs={'class': 'input'}),
            'value': forms.NumberInput(attrs={'class': 'input'}),
            'from_date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'to_date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'receipt_number': forms.TextInput(attrs={'class': 'input'}),
            'receipt_file': forms.FileInput(attrs={'class': 'input'}),
            'other_text': forms.TextInput(attrs={'class': 'input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter item queryset
        self.fields['item'].queryset = Item.objects.filter(type_choice='revenues')

        # Now control fields based on instance data
        instance = kwargs.get('instance')
        if instance and instance.pk:
            if instance.item:
                if not instance.item.name.strip() == 'أخري':
                    if 'other_text' in self.fields:
                        self.fields['other_text'].widget = forms.HiddenInput()
                        self.fields['other_text'].required = False

RevenueItemFormSet = inlineformset_factory(
    Revenue,RevenueItem,
    form=RevenueItemForm,
    fields='__all__',
    extra=0,  
    can_delete=True,
)

class ReportForm(forms.Form):
    city = forms.ModelChoiceField(
        label=_("City"),
        queryset=City.objects.all(),
        required=False,
        # empty_label=_("Select a city"),
        empty_label=_("Select"),
        widget=forms.Select(attrs={'class': 'input'})
    )
    region = forms.ModelChoiceField(
        label=_("Region"),
        queryset=Region.objects.all(),
        required=False,
        # empty_label=_("Select a region"),
        empty_label=_("Select"),
        widget=forms.Select(attrs={'class': 'input'})
    )
    district = forms.ModelChoiceField(
        label=_("District"),
        queryset=District.objects.all(),
        required=False,
        # empty_label=_("Select a district"),
        empty_label=_("Select"),
        widget=forms.Select(attrs={'class': 'input'})
    )
    town = forms.ModelChoiceField(
        label=_("Town"),
        queryset=Town.objects.all(),
        required=False,
        # empty_label=_("Select a town"),
        empty_label=_("Select"),
        widget=forms.Select(attrs={'class': 'input'})
    )
    neighborhood = forms.ModelChoiceField(
        label=_("Neighborhood"),
        queryset=Neighborhood.objects.all(),
        required=False,
        # empty_label=_("Select a neighborhood"),
        empty_label=_("Select"),
        widget=forms.Select(attrs={'class': 'input'})
    )
    from_date = forms.DateField(
        label=_("From Date"),
        required=False,
        widget=forms.DateInput(attrs={'class': 'input', 'type': 'date'})
    )
    to = forms.DateField(
        label=_("To Date"),
        required=False,
        widget=forms.DateInput(attrs={'class': 'input', 'type': 'date'})
    )
