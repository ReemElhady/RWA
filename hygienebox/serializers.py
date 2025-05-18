from rest_framework import serializers
from .models import Contract, Expense, ExpenseItem, Item, Revenue, RevenueItem

class ContractSerializer(serializers.ModelSerializer):
    down_payment_value = serializers.IntegerField(required=False, allow_null=True)
    down_payment_percentage = serializers.FloatField(required=False, allow_null=True)

    class Meta:
        model = Contract
        fields = '__all__'

class ExpenseItemSerializer(serializers.ModelSerializer):
    item = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all())
    
    class Meta:
        model = ExpenseItem
        fields = '__all__'
        extra_kwargs = {
            'expense': {'required': False},  
        }

class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = '__all__'
        read_only_fields = ['id']
        
        
class RevenueItemSerializer(serializers.ModelSerializer):
    item = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all())
    
    class Meta:
        model = RevenueItem
        fields = '__all__'
        extra_kwargs = {
            'revenue': {'required': False},  
        }

class RevenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Revenue
        fields = '__all__'
        read_only_fields = ['id']