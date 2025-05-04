from django.contrib import admin
from .models import (
    Item, Contract, Expense, ExpenseItem, Revenue, RevenueItem, RevenueDistribution
)

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('id','provider_name', 'city', 'region', 'contract_date', 'end_date', 'value', 'remaining', 'entry_date')
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
    list_display = ('register_number', 'created_at', 'city', 'region', 'total_expenses_display')
    search_fields = ('register_number',)
    list_filter = ('city', 'region', 'created_at')
    filter_horizontal = ('districts', 'towns', 'neighborhoods')
    date_hierarchy = 'created_at'
    readonly_fields = ('register_number', 'created_at', 'total_expenses_display')  
    fieldsets = (
        (None, {
            'fields': ('register_number',)
        }),
        ('Location', {
            'fields': ('city', 'region', 'districts', 'towns', 'neighborhoods')
        }),
        ('Info', {  
            'fields': ('created_at', 'total_expenses_display')
        })
    )

    def total_expenses_display(self, obj):
        return obj.total_expenses
    total_expenses_display.short_description = "Total Expenses (EGP)"
    total_expenses_display.admin_order_field = 'total_expenses'


@admin.register(ExpenseItem)
class ExpenseItemAdmin(admin.ModelAdmin):
    list_display = ('expense', 'item', 'contract', 'value', 'taxes', 'hanged_value', 'amount_due', 'on_date', 'receipt_number', 'receipt_file','other_text')
    search_fields = ('receipt_number', 'item__name', 'expense__register_number')
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
            'fields': ('on_date', 'receipt_number', 'receipt_file', 'other_text')
        }),
    )



#Revenues
@admin.register(Revenue)
class RevenueAdmin(admin.ModelAdmin):
    list_display = ('register_number', 'created_at', 'city', 'region', 'total_revenues_display')
    search_fields = ('register_number',)
    list_filter = ('city', 'region', 'created_at')
    filter_horizontal = ('districts', 'towns', 'neighborhoods')
    date_hierarchy = 'created_at'
    readonly_fields = ('register_number', 'created_at', 'total_revenues_display') 
    fieldsets = (
        (None, {
            'fields': ('register_number',) 
        }),
        ('Location', {
            'fields': ('city', 'region', 'districts', 'towns', 'neighborhoods')
        }),
        ('Info', { 
            'fields': ('created_at', 'total_revenues_display')
        })
    )

    def total_revenues_display(self, obj):
        return obj.total_revenues
    total_revenues_display.short_description = "Total Revenues (EGP)"
    total_revenues_display.admin_order_field = 'total_revenues'


@admin.register(RevenueItem)
class RevenueItemAdmin(admin.ModelAdmin):
    list_display = ('revenue', 'item', 'value', 'from_date', 'to_date', 'receipt_number', 'receipt_file', 'other_text')
    search_fields = ('receipt_number', 'item__name', 'revenue__register_number')
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
            'fields': ('receipt_number', 'receipt_file', 'other_text')
        }),
    )

@admin.register(RevenueDistribution)
class RevenueDistributionAdmin(admin.ModelAdmin):
    list_display = ('revenue_item', 'month', 'amount')
    list_filter = ('month',)
    search_fields = ('revenue_item__revenue__register_number', 'revenue_item__item__name')
    ordering = ('-month',)
