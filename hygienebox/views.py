from django.shortcuts import render , redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, renderer_classes
from django.views.decorators.http import require_POST
from rest_framework.decorators import parser_classes
from hygienebox.decorators import group_required
from django.db.models import Sum, Value , Q
from django.db.models.functions import Coalesce
from rest_framework.response import Response
from rest_framework import status
from .models import Expense ,Item , Contract, Revenue, ExpenseItem, RevenueItem
from .serializers import ContractSerializer, ExpenseSerializer, ExpenseItemSerializer, RevenueSerializer, RevenueItemSerializer
from .forms import ContractForm, ExpenseForm, ExpenseItemFormSet, RevenueForm, RevenueItemFormSet, ReportForm
from django.http import JsonResponse
from core.models import City, Region, District, Town, Neighborhood
from rest_framework.renderers import JSONRenderer
from django.db import transaction
from rest_framework import parsers
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from collections import OrderedDict

@login_required
@group_required('Admin','Editor','Viewer')
def dashboard(request):
    total_expense = Expense.objects.aggregate(total=Sum('expense_items__value'))['total'] or 0
    total_revenue = RevenueItem.objects.aggregate(total=Sum('value'))['total'] or 0
    total_contract = Contract.objects.aggregate(total=Sum('value'))['total'] or 0
    report_form = ReportForm(request.GET or None)

    from_date_str = request.GET.get('from_date')
    to_date_str = request.GET.get('to_date')

    today = datetime.today()
    current_year = today.year

    if from_date_str and to_date_str:
        from_date = datetime.strptime(from_date_str, "%Y-%m-%d")
        to_date = datetime.strptime(to_date_str, "%Y-%m-%d")
    else:
        from_date = datetime(current_year, 1, 1)
        to_date = datetime(current_year, 12, 31)

    # Filters
    date_filter_revenue = Q(from_date__range=(from_date, to_date))
    date_filter_expense = Q(on_date__range=(from_date, to_date))

    # Region charts
    region_revenues = []
    region_expenses = []
    region_names = []

    for region in Region.objects.all():
        rev_total = RevenueItem.objects.filter(
            revenue__region=region
        ).filter(date_filter_revenue).aggregate(total=Sum('value'))['total'] or 0

        exp_total = ExpenseItem.objects.filter(
            expense__regions=region 
        ).filter(date_filter_expense).aggregate(total=Sum('value'))['total'] or 0

        region_names.append(region.name)
        region_revenues.append(rev_total)
        region_expenses.append(exp_total)


    # Determine interval
    delta_days = (to_date - from_date).days
    if delta_days <= 31:
        interval_type = 'daily'
    elif delta_days <= 366:
        interval_type = 'monthly'
    else:
        interval_type = 'yearly'

    # Trend chart
    labels = []
    revenue_totals = []
    expense_totals = []

    current = from_date

    while current <= to_date:
        if interval_type == 'daily':
            next_interval = current + timedelta(days=1)
            label = current.strftime('%d %b')
        elif interval_type == 'monthly':
            next_interval = current + relativedelta(months=1)
            label = current.strftime('%B')
        else:  # yearly
            next_interval = current + relativedelta(years=1)
            label = current.strftime('%Y')

        rev_total = RevenueItem.objects.filter(
            from_date__gte=current,
            from_date__lt=next_interval
        ).aggregate(total=Sum('value'))['total'] or 0

        exp_total = ExpenseItem.objects.filter(
            on_date__gte=current,
            on_date__lt=next_interval
        ).aggregate(total=Sum('value'))['total'] or 0

        labels.append(label)
        revenue_totals.append(rev_total)
        expense_totals.append(exp_total)

        current = next_interval
        
    contract_expense_total = ExpenseItem.objects.filter(
        contract__isnull=False
    ).aggregate(total=Sum('value'))['total'] or 0

    non_contract_expense_total = total_expense - contract_expense_total
    
    context = {
        'months': labels,
        'revenue_monthly_totals': revenue_totals,
        'expense_monthly_totals': expense_totals,
        'report_form': report_form,
        'total_expense': total_expense,
        'total_revenue': total_revenue,
        'total_contract': total_contract,
        'region_names': region_names,
        'region_revenues': region_revenues,
        'region_expenses': region_expenses,
        'from_date': from_date_str,
        'to_date': to_date_str,
        'contract_expense_total': contract_expense_total,
        'non_contract_expense_total': non_contract_expense_total,
    }

    return render(request, 'hygienebox/dashboard.html', context)

#Contracts
@api_view(['POST'])
@renderer_classes([JSONRenderer])
@group_required('Admin','Editor')
def create_contract(request):
    if request.method == 'GET':
        return Response({'detail': 'Please submit contract data via POST.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    print("Request Data",request.data )
    serializer = ContractSerializer(data=request.data)
    if serializer.is_valid():
        print("Validated Data", serializer.validated_data)
        contract = serializer.save() 
        if not contract.created_by:
            contract.created_by = request.user  
        else:
            contract.updated_by = request.user  

        contract.save()  
        return JsonResponse({'message': 'Contract created successfully', 'redirect': '/hygienebox/contracts/'})
    # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return JsonResponse({'errors': serializer.errors}, status=400)

def contract_form_view(request):
    cities = City.objects.all()
    return render(request, 'hygienebox/contract_create.html', {'cities': cities})

def get_regions(request):
    city_id = request.GET.get('city_id')
    regions = Region.objects.filter(country_id=city_id).values('id', 'name')
    return JsonResponse(list(regions), safe=False)

def get_districts(request):
    region_param = request.GET.get('region_id') or request.GET.get('region_ids')
    if region_param:
        region_ids = [int(i) for i in region_param.split(',') if i.isdigit()]
        districts = District.objects.filter(region_id__in=region_ids).select_related('region')
        data = [{'id': d.id, 'name': f"{d.name} ({d.region.name})"} for d in districts]
    else:
        data = []
    return JsonResponse(data, safe=False)

def get_towns(request):
    district_param = request.GET.get('district_id') or request.GET.get('district_ids')
    if district_param:
        district_ids = [int(i) for i in district_param.split(',') if i.isdigit()]
        towns = Town.objects.filter(district_id__in=district_ids).select_related('district')
        data = [{'id': t.id, 'name': f"{t.name} ({t.district.name})"} for t in towns]
    else:
        data = []
    return JsonResponse(data, safe=False)

def get_neighborhoods(request):
    town_param = request.GET.get('town_id') or request.GET.get('town_ids')
    if town_param:
        town_ids = [int(i) for i in town_param.split(',') if i.isdigit()]
        neighborhoods = Neighborhood.objects.filter(town_id__in=town_ids).select_related('town')
        data = [{'id': n.id, 'name': f"{n.name} ({n.town.name})"} for n in neighborhoods]
    else:
        data = []
    return JsonResponse(data, safe=False)

def get_committed_areas(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)

    committed_regions = set()
    if contract.region:
        committed_regions.add(contract.region)
    if contract.city:
        committed_regions.update(contract.city.regions.all())

    committed_districts = set(contract.districts.all())
    for region in committed_regions:
        if not committed_districts.intersection(region.districts.all()):
            committed_districts.update(region.districts.all())

    committed_towns = set(contract.towns.all())
    for district in committed_districts:
        if not committed_towns.intersection(district.towns.all()):
            committed_towns.update(district.towns.all())

    committed_neighborhoods = set(contract.neighborhoods.all())
    for town in committed_towns:
        if not committed_neighborhoods.intersection(town.neighborhoods.all()):
            committed_neighborhoods.update(town.neighborhoods.all())

    context = {
        'contract': contract,
        'regions': committed_regions,
        'districts': committed_districts,
        'towns': committed_towns,
        'neighborhoods': committed_neighborhoods,
    }
    return render(request, 'hygienebox/committed_areas.html', context)

def contract_list_view(request):
    contracts = Contract.objects.all().distinct()
    cities = City.objects.all()

    city = request.GET.get('city')
    region = request.GET.get('region')
    district = request.GET.get('district')
    town = request.GET.get('town')
    neighborhood = request.GET.get('neighborhood')

    if city:
        contracts = contracts.filter(city_id=city)
    if region:
        contracts = contracts.filter(region_id=region)
    if district:
        contracts = contracts.filter(districts__id=district)
    if town:
        contracts = contracts.filter(towns__id=town)
    if neighborhood:
        contracts = contracts.filter(neighborhoods__id=neighborhood)

    context = {
        'contract_list': contracts.distinct(),
        'cities': cities,
    }

    return render(request, 'hygienebox/contract_list.html', context)

@group_required('Admin')
def edit_contract(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)
    cities = City.objects.all()

    if request.method == 'POST':
        form = ContractForm(request.POST, instance=contract)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.updated_by = request.user
            instance.save()
            return redirect('contracts')
    else:
        form = ContractForm(instance=contract)

    return render(request, 'hygienebox/contract_edit.html', {'form': form, 'contract': contract, 'cities': cities})

@require_POST
@group_required('Admin')
def delete_contract(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)
    contract.delete()
    return redirect('contracts')

def contract_analytics_view(request, contract_id):
    contract = get_object_or_404(Contract, id=contract_id)
    expected = contract.expected_payments.all().order_by('payment_date')

    data = OrderedDict()

    for ep in expected:
        month_key = ep.payment_date.strftime('%Y-%m')  
        label = ep.payment_date.strftime('%b %Y')   

        actual_paid = ExpenseItem.objects.filter(
            contract=contract,
            on_date__year=ep.payment_date.year,
            on_date__month=ep.payment_date.month
        ).aggregate(total=Sum('value'))['total'] or 0

        data[label] = {
            'expected': float(ep.amount),
            'actual': float(actual_paid)
        }

    context = {
        'contract': contract,
        'chart_labels': list(data.keys()),
        'expected_values': [v['expected'] for v in data.values()],
        'actual_values': [v['actual'] for v in data.values()],
    }

    return render(request, 'hygienebox/contract_analytics.html', context)

#Expenses
@api_view(['POST'])
@parser_classes([parsers.MultiPartParser, parsers.FormParser])
@renderer_classes([JSONRenderer])
@group_required('Admin','Editor')
def create_expense(request):
    try:
        with transaction.atomic():
            data = request.data.copy()
            
            # Debug raw data
            # print("Raw data received:", data)
            
            # Parse expense_items if exists
            expense_items = []
            if 'expense_items' in data:
                try:
                    expense_items = json.loads(data['expense_items'])
                    # print("Parsed expense_items:", expense_items)
                except (json.JSONDecodeError, TypeError) as e:
                    # print("Error parsing expense_items:", str(e))
                    return Response(
                        {'error': 'Invalid expense_items format'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Manually validate we have expense items
            if not expense_items:
                return Response(
                    {'expense_items': 'This field is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if contract exists in any item
            contract_id = None
            for item in expense_items:
                if item.get('contract'):
                    contract_id = item['contract']
                    break

            contract_instance = None
            if contract_id:
                contract_instance = Contract.objects.select_related('city', 'region').prefetch_related('districts', 'towns', 'neighborhoods').filter(id=contract_id).first()

            # Prepare main expense data
            if contract_instance:
                # If Contract is selected, pull data from Contract
                expense_data = {
                    'city': contract_instance.city.id if contract_instance.city else None,
                    'regions': [contract_instance.region.id] if contract_instance.region else [],
                    'districts': [d.id for d in contract_instance.districts.all()],
                    'towns': [t.id for t in contract_instance.towns.all()],
                    'neighborhoods': [n.id for n in contract_instance.neighborhoods.all()],
                    'receipt_number': data.get('receipt_number'),
                    'receipt_date': data.get('receipt_date'),
                    'receipt_file': request.FILES.get('receipt_file'),

                }
            else:
                user_city = request.user.profile.city
                expense_data = {
                    'city': user_city.id if user_city else None,
                    'regions': data.getlist('regions'),
                    'districts': data.getlist('districts'),
                    'towns': data.getlist('towns'),
                    'neighborhoods': data.getlist('neighborhoods'),
                    'receipt_number': data.get('receipt_number'),
                    'receipt_date': data.get('receipt_date'),
                    'receipt_file': request.FILES.get('receipt_file'),
                }


            # Create Expense
            expense_serializer = ExpenseSerializer(data=expense_data, context={'request': request})
            if not expense_serializer.is_valid():
                return Response(expense_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            expense = expense_serializer.save()
            expense.save(user=request.user)
            

            
            for idx, item_data in enumerate(expense_items):
                item_serializer = ExpenseItemSerializer(data=item_data, context={
                    'request': request,
                    'expense': expense
                })
                
                if not item_serializer.is_valid():
                    return Response(
                        {'expense_items': {str(idx): item_serializer.errors}},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                item_serializer.save(expense=expense)
            
            return JsonResponse({
                'message': 'Expense created successfully',
                'redirect': '/hygienebox/expenses/list/'
            })
            
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
def expense_form_view(request):
    cities = City.objects.all()
    items = Item.objects.filter(type_choice='expenses')
    contracts = Contract.objects.all()
    user_city = getattr(request.user.profile, 'city', None)

    return render(request, 'hygienebox/expense_create.html', {
        'cities': cities,
        'items': items,
        'contracts': contracts,
        'user_city': user_city,
    })

def expense_list_view(request):
    expense = Expense.objects.all().distinct()
    cities = City.objects.all()

    city = request.GET.get('city')
    region = request.GET.get('region') 
    district = request.GET.get('district')
    town = request.GET.get('town')
    neighborhood = request.GET.get('neighborhood')

    if city:
        expense = expense.filter(city_id=city)
    if region:
       expense = expense.filter(regions__id=region)
    if district:
        expense = expense.filter(districts__id=district)
    if town:
        expense = expense.filter(towns__id=town)
    if neighborhood:
        expense = expense.filter(neighborhoods__id=neighborhood)

    context = {
        'expense_list': expense.distinct(),
        'cities': cities,
    }

    return render(request, 'hygienebox/expense_list.html', context)

@group_required('Admin')
def edit_expense(request, expense_id):
    expense = get_object_or_404(Expense, pk=expense_id)
    cities = City.objects.all()

    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        formset = ExpenseItemFormSet(request.POST, request.FILES, instance=expense)

        if form.is_valid() and formset.is_valid():
            instance = form.save(commit=False)
            instance.updated_by = request.user
            instance.save()
            formset.save()
            return redirect('expenses_list')
        else:
            print("Form errors:", form.errors)
            print("Formset errors:", formset.errors)
    else:
        form = ExpenseForm(instance=expense)
        formset = ExpenseItemFormSet(instance=expense)

    return render(request, 'hygienebox/expense_edit.html', {
        'expense_form': form,
        'items_formset': formset,
        'expense': expense,
        'cities': cities,
    })

@require_POST
@group_required('Admin')
def delete_expense(request, expense_id):
    expense = get_object_or_404(Expense, pk=expense_id)
    expense.delete()
    return redirect('expenses_list')


#Revenues
@api_view(['POST'])
@parser_classes([parsers.MultiPartParser, parsers.FormParser])
@renderer_classes([JSONRenderer])
@group_required('Admin','Editor')
def create_revenue(request):
    try:
        with transaction.atomic():
            data = request.data.copy()
            
            # Debug raw data
            print("Raw data received:", data)
            
            revenue_items = []
            if 'revenue_items' in data:
                try:
                    revenue_items = json.loads(data['revenue_items'])
                    print("Parsed revenue_items:", revenue_items)
                except (json.JSONDecodeError, TypeError) as e:
                    print("Error parsing revenue_items:", str(e))
                    return Response(
                        {'error': 'Invalid revenue_items format'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            if not revenue_items:
                return Response(
                    {'revenue_items': 'This field is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user_city = request.user.profile.city
            revenue_data = {
                'city': user_city.id if user_city else None,
                'region': data.getlist('region'),
                'receipt_number': data.get('receipt_number'),
                'receipt_file': request.FILES.get('receipt_file'),
                'receipt_date': data.get('receipt_date'),
            }


            # Create Revenue
            revenue_serializer = RevenueSerializer(data=revenue_data, context={'request': request})
            if not revenue_serializer.is_valid():
                return Response(revenue_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            revenue = revenue_serializer.save()
            revenue.save(user=request.user)


            
            # Process each revenue item
            for idx, item_data in enumerate(revenue_items):
                # Create revenue item
                item_serializer = RevenueItemSerializer(data=item_data, context={
                    'request': request,
                    'revenue': revenue
                })
                
                if not item_serializer.is_valid():
                    return Response(
                        {'revenue_items': {str(idx): item_serializer.errors}},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                item_serializer.save(revenue=revenue)
                
            
            return JsonResponse({
                'message': 'Revenue created successfully',
                'redirect': '/hygienebox/revenues/list/'
            })
            
    except Exception as e:
        # print("Error creating expense:", str(e))
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def revenue_form_view(request):
    user_city = request.user.profile.city
    items = Item.objects.filter(type_choice='revenues')
    return render(request, 'hygienebox/revenue_create.html', {
        'user_city_id': user_city.id if user_city else None,
        'items': items
    })

def revenues_list_view(request):
    user_city = request.user.profile.city
    revenue = Revenue.objects.filter(city=user_city).distinct()

    region = request.GET.get('region')
    if region:
        revenue = revenue.filter(region__id=region)

    # Get regions linked to the user's city
    regions = Region.objects.filter(country=user_city)

    context = {
        'revenue_list': revenue,
        'regions': regions,
        'selected_region': region,
    }

    return render(request, 'hygienebox/revenue_list.html', context)

@group_required('Admin')
def edit_revenue(request, revenue_id):
    revenue = get_object_or_404(Revenue, pk=revenue_id)
    cities = City.objects.all()

    if request.method == 'POST':
        form = RevenueForm(request.POST, instance=revenue)
        formset = RevenueItemFormSet(request.POST, request.FILES, instance=revenue)

        if form.is_valid() and formset.is_valid():
            instance = form.save(commit=False)
            instance.updated_by = request.user
            instance.save()
            form.save_m2m()
            formset.save()
            return redirect('revenues_list')
        else:
            print("Form errors:", form.errors)
            print("Formset errors:", formset.errors)
    else:
        form = RevenueForm(instance=revenue)
        formset = RevenueItemFormSet(instance=revenue)

    return render(request, 'hygienebox/revenue_edit.html', {
        'revenue_form': form,
        'items_formset': formset,
        'revenue': revenue,
        'cities': cities,
    })
    
@require_POST
@group_required('Admin')
def delete_revenue(request, revenue_id):
    revenue = get_object_or_404(Revenue, pk=revenue_id)
    revenue.delete()
    return redirect('revenues_list')

@login_required
def reports(request):
    report_form = ReportForm(request.POST or None)
    expense_item_labels = []
    expense_item_values = []
    revenue_item_labels = []
    revenue_item_values = []

    filters_revenue = Q()
    filters_expense = Q()

    if request.method == 'POST' and report_form.is_valid():
        city = report_form.cleaned_data.get('city')
        region = report_form.cleaned_data.get('region')
        from_date = report_form.cleaned_data.get('from_date')
        to_date = report_form.cleaned_data.get('to')

        if city:
            filters_revenue &= Q(revenueitem__revenue__city=city)
            filters_expense &= Q(expenseitem__expense__city=city)

        if region:
            filters_revenue &= Q(revenueitem__revenue__region=region)
            filters_expense &= Q(expenseitem__expense__regions=region)  # ✅ Use correct M2M field

        if from_date and to_date:
            filters_revenue &= Q(revenueitem__revenue__receipt_date__range=(from_date, to_date))
            filters_expense &= Q(expenseitem__on_date__range=(from_date, to_date))
        elif from_date:
            filters_revenue &= Q(revenueitem__revenue__receipt_date__gte=from_date)
            filters_expense &= Q(expenseitem__on_date__gte=from_date)
        elif to_date:
            filters_revenue &= Q(revenueitem__revenue__receipt_date__lte=to_date)
            filters_expense &= Q(expenseitem__on_date__lte=to_date)

    # Revenue Aggregation by Item
    revenues = (
        Item.objects.filter(type_choice="revenues")
        .annotate(
            total_value=Coalesce(Sum('revenueitem__value', filter=filters_revenue), Value(0))
        )
        .values('name', 'total_value')
    )

    # Expense Aggregation by Item
    expenses = (
        Item.objects.filter(type_choice="expenses")
        .annotate(
            total_value=Coalesce(Sum('expenseitem__value', filter=filters_expense), Value(0))
        )
        .values('name', 'total_value')
    )

    for item in revenues:
        revenue_item_labels.append(item['name'])
        revenue_item_values.append(item['total_value'])

    for item in expenses:
        expense_item_labels.append(item['name'])
        expense_item_values.append(item['total_value'])

    return render(
        request,
        'hygienebox/reports.html',
        {
            'report_form': report_form,
            'expense_item_labels': expense_item_labels,
            'expense_item_values': expense_item_values,
            'revenue_item_labels': revenue_item_labels,
            'revenue_item_values': revenue_item_values,
        }
    )
