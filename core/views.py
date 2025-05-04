from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import City
from hygienebox.models import Expense
from django.db.models import Sum
# Create your views here.

@login_required
def dashboard(request):
    total_expense = Expense.objects.all().aggregate(total=Sum('expense_items__value'))['total'] or 0
    
    return render(request , 'hygienebox/dashboard.html',{
                                                        'total_expense':total_expense,
                                                        })
# def dashboard(request):
#     cities = City.objects.all()
#     return render(request,'index.html',{'cities':cities})
