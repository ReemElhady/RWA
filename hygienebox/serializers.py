from rest_framework import serializers
from .models import Contract, Expense, ExpenseItem, Item, Revenue, RevenueItem

class ContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = '__all__'

class ExpenseItemSerializer(serializers.ModelSerializer):
    item = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all())
    
    class Meta:
        model = ExpenseItem
        fields = '__all__'
        extra_kwargs = {
            'expense': {'required': False},  # Will be set manually
        }

class ExpenseSerializer(serializers.ModelSerializer):
    # Remove the nested expense_items from the serializer
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
            'revenue': {'required': False},  # Will be set manually
        }

class RevenueSerializer(serializers.ModelSerializer):
    # Remove the nested expense_items from the serializer
    class Meta:
        model = Revenue
        fields = '__all__'
        read_only_fields = ['id']