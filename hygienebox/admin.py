from django.contrib import admin
from .models import RevenueReg , ExpenseReg, Contract , ServiceProvider , RevenueItem ,ExpenseItem, Item
from simple_history.admin import SimpleHistoryAdmin

# Register your models here.

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display=('name','type_choice')
@admin.register(RevenueReg)
class RevenueRegAdmin(admin.ModelAdmin):
    exclude = ('register_number',)  # This hides the field
    list_display=('register_number',)

@admin.register(ExpenseReg)
class ExpenseRegAdmin(admin.ModelAdmin):
    exclude = ('register_number',)  # This hides the field
    list_display=('register_number',)
    
admin.site.register(RevenueItem,SimpleHistoryAdmin)
admin.site.register(ExpenseItem,SimpleHistoryAdmin)

admin.site.register(ServiceProvider)
admin.site.register(Contract)