from django.contrib import admin
from .models import (
    Item, Contract, Expense, ExpenseItem, Revenue, RevenueItem, ExpectedPayment
)

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('id','provider_name', 'city', 'region', 'contract_date', 'end_date', 'value', 'down_payment_percentage', 'down_payment_value', 'remaining','payment_frequency', 'entry_date')
    search_fields = ('provider_name',)
    list_filter = ('city', 'region', 'contract_date')
    filter_horizontal = ('districts', 'towns', 'neighborhoods')

# Base Item admin
@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'type_choice')
    search_fields = ('name',)

#Expenses
@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('register_number', 'created_at', 'city', 'get_regions', 'receipt_number', 'receipt_date', 'receipt_file', 'total_expenses_display')
    search_fields = ('register_number', 'receipt_number')
    list_filter = ('city', 'regions', 'created_at')
    filter_horizontal = ('districts', 'towns', 'neighborhoods')
    date_hierarchy = 'created_at'
    readonly_fields = ('register_number', 'created_at', 'total_expenses_display')  
    fieldsets = (
        (None, {
            'fields': ('register_number', 'receipt_number', 'receipt_file', 'receipt_date')
        }),
        ('Location', {
            'fields': ('city', 'regions', 'districts', 'towns', 'neighborhoods')
        }),
        ('Info', {  
            'fields': ('created_at', 'total_expenses_display')
        })
    )

    def get_regions(self, obj):
        return ", ".join([region.name for region in obj.regions.all()])
    get_regions.short_description = "Regions"
    
    def total_expenses_display(self, obj):
        return obj.total_expenses
    total_expenses_display.short_description = "Total Expenses (EGP)"
    total_expenses_display.admin_order_field = 'total_expenses'


@admin.register(ExpenseItem)
class ExpenseItemAdmin(admin.ModelAdmin):
    list_display = ('expense', 'item', 'contract', 'value', 'taxes', 'hanged_value', 'amount_due', 'paid_for', 'on_date','other_text')
    search_fields = ('item__name', 'expense__register_number')
    list_filter = ('on_date', 'item')
    autocomplete_fields = ('expense', 'item', 'contract') 
    readonly_fields = ('expense',)
    fieldsets = (
        (None, {
            'fields': ('expense', 'item', 'contract')
        }),
        ('Financials', {
            'fields': ('value', 'taxes', 'hanged_value', 'amount_due')
        }),
        ('Documentation', {
            'fields': ('on_date', 'paid_for', 'other_text')
        }),
    )



#Revenues
@admin.register(Revenue)
class RevenueAdmin(admin.ModelAdmin):
    list_display = (
        'register_number', 'created_at', 'city', 'region_list', 'receipt_number', 'receipt_date', 'receipt_file', 'total_revenues_display'
    )
    search_fields = ('register_number', 'receipt_number')
    list_filter = ('city', 'region', 'created_at')
    date_hierarchy = 'created_at'
    readonly_fields = ('register_number', 'created_at', 'total_revenues_display')
    fieldsets = (
        (None, {
            'fields': ('register_number', 'receipt_number', 'receipt_file', 'receipt_date')
        }),
        ('Location', {
            'fields': ('city', 'region')
        }),
        ('Info', {
            'fields': ('created_at', 'total_revenues_display')
        })
    )
    
    def region_list(self, obj):
            return ", ".join(region.name for region in obj.region.all())
    region_list.short_description = "Regions"

    def total_revenues_display(self, obj):
        return obj.total_revenues
    total_revenues_display.short_description = "Total Revenues (EGP)"



@admin.register(RevenueItem)
class RevenueItemAdmin(admin.ModelAdmin):
    list_display = ('revenue', 'item', 'value', 'from_date', 'to_date', 'other_text')
    search_fields = ('item__name', 'revenue__register_number')
    list_filter = ('item',)
    autocomplete_fields = ('revenue', 'item') 
    readonly_fields = ('revenue',)
    fieldsets = (
        (None, {
            'fields': ('revenue', 'item')
        }),
        ('Financials', {
            'fields': ('value',)
        }),
        ('Documentation', {
            'fields': ('other_text',)
        }),
    )

@admin.register(ExpectedPayment)
class ExpectedPaymentAdmin(admin.ModelAdmin):
    list_display = ('contract', 'payment_date', 'amount')
    list_filter = ('payment_date',)
    ordering = ('-payment_date',)
