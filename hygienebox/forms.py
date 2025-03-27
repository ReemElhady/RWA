from ast import arg
from .models import Item, RevenueReg, RevenueItem , ExpenseReg , ExpenseItem , Contract
from django import forms
from django.forms import modelformset_factory
from core.models import Area, Neighborhood

class RevenueForm(forms.ModelForm):
    class Meta:
        model = RevenueReg
        fields = ['site', 'neighborhood']
        # success_url = reverse_lazy('hygienebox_dashboard')
        widgets = {
            'site': forms.Select(attrs={'class': 'input'}),
            'neighborhood': forms.Select(attrs={'class': 'input'}),
        }
    
    # def __init__(self,*args,**kwargs):
    #     super().__init__(*args,**kwargs)
    #     if not self.instance.pk:
    #         self.fields['neighborhood'].queryset = Neighborhood.objects.none()         
        
class RevenueItemForm(forms.ModelForm):
    class Meta:
        model = RevenueItem
        fields = ['revenue','item','value','other_title','from_date','to_date']
        # success_url = reverse_lazy('hygienebox_dashboard')
        widgets = {
            'revenue': forms.Select(attrs={'class': 'input'}),
            'item': forms.Select(attrs={'class': 'input'}),
            'other_title': forms.TextInput(attrs={'class': 'input'}),
            'value': forms.NumberInput(attrs={'class': 'input'}),
            'from_date': forms.DateInput(attrs={'class': 'input', 'type': 'date',}),
            'to_date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
        }
    def __init__(self,*args , **kwargs):
        super().__init__(*args , **kwargs)
        self.fields['item'].queryset = Item.objects.filter(type_choice='revenues')

    def clean(self):
        cleaned_data = super().clean()
        site = cleaned_data.get('site')
        neighborhood = cleaned_data.get('neighborhood')
        from_date = cleaned_data.get('from_date')
        to_date = cleaned_data.get('to_date')
        # ✅ Rule 1: Ensure neighborhood is only selected if a site is chosen
        if neighborhood and not site:
            self.add_error('neighborhood', "You must select a site first before choosing a neighborhood.")

        # ✅ Rule 2: Ensure "from_date" is before "to_date"
        if from_date and to_date and from_date > to_date:
            self.add_error('to_date', "End date must be after start date.")

        # ✅ Rule 3: Ensure at least one filter is applied
        if not site and not from_date and not to_date:
            raise forms.ValidationError("Please select at least a site or a date range to filter the report.")

        return cleaned_data

RevenueItemFormSet = modelformset_factory(
    RevenueItem,
    form=RevenueItemForm,
    fields=["id","item", "value", "other_title", "from_date", "to_date"],
    extra=1,  # Keep the extra row for new entries
    can_delete=True,
    validate_max=False,
    validate_min=False,  # Ensure partial forms don't break
)

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = ExpenseReg
        fields = ['site', 'neighborhood']
        # success_url = reverse_lazy('hygienebox_dashboard')
        widgets = {
            'site': forms.Select(attrs={'class': 'input'}),
            'neighborhood': forms.Select(attrs={'class': 'input'}),
        }
    # def __init__(self,*args,**kwargs):
    #     super().__init__(*args,**kwargs)
    #     if not self.instance.pk:
    #         self.fields['neighborhood'].queryset = Neighborhood.objects.none()
    #     if "site" in self.data:
    #         try:
    #             site_id = int(self.data.get("site"))
    #             self.fields["neighborhood"].queryset = Neighborhood.objects.filter(area_id=site_id)
    #         except (ValueError, TypeError):
    #             pass
class ExpenseItemForm(forms.ModelForm):
    class Meta:
        model = ExpenseItem
        fields = ['id','expense','item','value','other_title','contract','from_date']
        # success_url = reverse_lazy('hygienebox_dashboard')
        widgets = {
            'expense': forms.Select(attrs={'class': 'input'}),
            'item': forms.Select(attrs={'class': 'input'}),
            'value': forms.NumberInput(attrs={'class': 'input'}),
            'other_title': forms.TextInput(attrs={'class': 'input'}),
            'contract': forms.Select(attrs={'class': 'input'}),
            'from_date': forms.DateInput(attrs={'class': 'input', 'type': 'date',}),
        }
    def __init__(self,*args , **kwargs):
        super().__init__(*args , **kwargs)
        self.fields['item'].queryset = Item.objects.filter(type_choice='expenses')
        
ExpenseItemFormSet = modelformset_factory(
    ExpenseItem,
    form=ExpenseItemForm,
    fields=["item", "value", "other_title",'contract', "from_date"],
    extra=1,  # Keep the extra row for new entries
    can_delete=True,
    validate_max=False,
    validate_min=False,  # Ensure partial forms don't break
)

class ContractForm(forms.ModelForm):
    # def __init__(self,*args,**kwargs):
    #     super().__init__(*args,**kwargs)
    #     if not self.instance.pk:
    #         self.fields['neighborhood'].queryset = Neighborhood.objects.none()
    class Meta:
        model = Contract
        fields = ['site','neighborhood','service_provider','value','from_date' , 'to_date']
        widgets = {
            'site': forms.Select(attrs={'class': 'input'}),
            'neighborhood': forms.Select(attrs={'class': 'input'}),
            'service_provider': forms.Select(attrs={'class': 'input'}),
            'value': forms.NumberInput(attrs={'class': 'input'}),
            'from_date': forms.DateInput(attrs={'class': 'input', 'type': 'date',}),
            'to_date': forms.DateInput(attrs={'class': 'input', 'type': 'date',}),

        }
    def clean(self):
        cleaned_data = super().clean()
        value = cleaned_data.get("value")
        start_date = cleaned_data.get("from_date")
        end_date = cleaned_data.get("to_date")
        if value and start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError("Start date must be before end date.")
            if value < 0:
                raise forms.ValidationError("Value must be positive.")
            return cleaned_data

class ReportForm(forms.Form):
    site = forms.ModelChoiceField(
        required=False,
        queryset=Area.objects.all(),
        empty_label="Select a site",
        widget=forms.Select(attrs={'class': 'input'})
    )
    neighborhood = forms.ModelChoiceField(
        required=False,
        queryset=Neighborhood.objects.none(),
        empty_label="Select a neighborhood",
        widget=forms.Select(attrs={'class': 'input','style':"width:250px"})
    )
    from_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'input', 'type': 'date'})
    )

    to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'input', 'type': 'date'})
    )
    # ✅ Custom initialization
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'site' in self.data:
            site_id = self.data.get('site')
            # ✅ If a site is selected, filter neighborhoods
            if site_id:
                self.fields['neighborhood'].queryset = Neighborhood.objects.filter(area_id=site_id)