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
from .models import Expense ,Item , Contract, Revenue, ExpenseItem, RevenueDistribution
from .serializers import ContractSerializer, ExpenseSerializer, ExpenseItemSerializer, RevenueSerializer, RevenueItemSerializer
from .forms import ContractForm, ExpenseForm, ExpenseItemFormSet, RevenueForm, RevenueItemFormSet, ReportForm
from django.http import JsonResponse
from core.models import City, Region, District, Town, Neighborhood
from rest_framework.renderers import JSONRenderer
from django.db import transaction
from rest_framework import parsers
import json
from datetime import datetime

@login_required
@group_required('Admin','Editor','Viewer')
def dashboard(request):
    total_expense = Expense.objects.aggregate(total=Sum('expense_items__value'))['total'] or 0
    total_revenue = Revenue.objects.aggregate(total=Sum('revenue_items__value'))['total'] or 0
    total_contract = Contract.objects.aggregate(total=Sum('value'))['total'] or 0
    report_form = ReportForm(request.GET or None)

    current_year = datetime.today().year

    months = []
    revenue_monthly_totals = []
    expense_monthly_totals = []

    # Filters (for new graphs)
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    date_filter_revenue = Q()
    date_filter_expense = Q()

    if from_date and to_date:
        date_filter_revenue = Q(month__range=(from_date, to_date))
        date_filter_expense = Q(on_date__range=(from_date, to_date))
    elif from_date:
        date_filter_revenue = Q(month__gte=from_date)
        date_filter_expense = Q(on_date__gte=from_date)
    elif to_date:
        date_filter_revenue = Q(month__lte=to_date)
        date_filter_expense = Q(on_date__lte=to_date)

    # Regions Revenues and Expenses
    region_revenues = []
    region_expenses = []
    region_names = []

    for region in Region.objects.all():
        # Revenues
        rev_total = RevenueDistribution.objects.filter(
            revenue_item__revenue__region=region
        ).filter(date_filter_revenue).aggregate(total=Sum('amount'))['total'] or 0
        
        # Expenses
        exp_total = ExpenseItem.objects.filter(
            expense__region=region
        ).filter(date_filter_expense).aggregate(total=Sum('value'))['total'] or 0
        
        region_names.append(region.name)
        region_revenues.append(rev_total)
        region_expenses.append(exp_total)

    # Monthly Trends
    for month in range(1, 13):
        start_date = datetime(current_year, month, 1)
        if month == 12:
            end_date = datetime(current_year + 1, 1, 1)
        else:
            end_date = datetime(current_year, month + 1, 1)

        revenue_sum = RevenueDistribution.objects.filter(
            month__gte=start_date,
            month__lt=end_date
        ).aggregate(total=Sum('amount'))['total'] or 0

        expense_sum = ExpenseItem.objects.filter(
            on_date__gte=start_date,
            on_date__lt=end_date
        ).aggregate(total=Sum('value'))['total'] or 0

        months.append(start_date.strftime('%B'))
        revenue_monthly_totals.append(revenue_sum)
        expense_monthly_totals.append(expense_sum)

    context = {
        'months': months,
        'revenue_monthly_totals': revenue_monthly_totals,
        'expense_monthly_totals': expense_monthly_totals,
        'report_form': report_form,
        'total_expense': total_expense,
        'total_revenue': total_revenue,
        'total_contract': total_contract,
        'region_names': region_names,
        'region_revenues': region_revenues,
        'region_expenses': region_expenses,
        'from_date': from_date,
        'to_date': to_date
    }
    return render(request, 'hygienebox/dashboard.html', context)

#Contracts
@api_view(['POST'])
@renderer_classes([JSONRenderer])
@group_required('Admin','Editor')
def create_contract(request):
    if request.method == 'GET':
        return Response({'detail': 'Please submit contract data via POST.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    serializer = ContractSerializer(data=request.data)
    if serializer.is_valid():
        contract = serializer.save() 
        if not contract.created_by:
            contract.created_by = request.user  
        else:
            contract.updated_by = request.user  

        contract.save()  
        return JsonResponse({'message': 'Contract created successfully', 'redirect': '/hygienebox/contracts/'})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def contract_form_view(request):
    cities = City.objects.all()
    return render(request, 'hygienebox/contract_create.html', {'cities': cities})

def get_regions(request):
    city_id = request.GET.get('city_id')
    regions = Region.objects.filter(country_id=city_id).values('id', 'name')
    return JsonResponse(list(regions), safe=False)

def get_districts(request):
    region_id = request.GET.get('region_id')
    districts = District.objects.filter(region_id=region_id).values('id', 'name')
    return JsonResponse(list(districts), safe=False)

def get_towns(request):
    district_ids = request.GET.get('district_ids', '').split(',')
    towns = Town.objects.filter(district_id__in=district_ids).values('id', 'name')
    return JsonResponse(list(towns), safe=False)

def get_neighborhoods(request):
    town_ids = request.GET.get('town_ids', '').split(',')
    neighborhoods = Neighborhood.objects.filter(town_id__in=town_ids).values('id', 'name')
    return JsonResponse(list(neighborhoods), safe=False)

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
                    'region': contract_instance.region.id if contract_instance.region else None,
                    'districts': [d.id for d in contract_instance.districts.all()],
                    'towns': [t.id for t in contract_instance.towns.all()],
                    'neighborhoods': [n.id for n in contract_instance.neighborhoods.all()],
                }
            else:
                expense_data = {
                    'city': data.get('city'),
                    'region': data.get('region'),
                    'districts': data.getlist('districts'),
                    'towns': data.getlist('towns'),
                    'neighborhoods': data.getlist('neighborhoods'),
                }

            # Create Expense
            expense_serializer = ExpenseSerializer(data=expense_data, context={'request': request})
            if not expense_serializer.is_valid():
                return Response(expense_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            expense = expense_serializer.save()
            expense.save(user=request.user)
            

            
            # Process each expense item
            for idx, item_data in enumerate(expense_items):
                # Handle file upload if specified
                file_key = item_data.get('receipt_file')
                if file_key and file_key in request.FILES:
                    item_data['receipt_file'] = request.FILES[file_key]
                
                # Create expense item
                item_serializer = ExpenseItemSerializer(data=item_data, context={
                    'request': request,
                    'expense': expense
                })
                
                if not item_serializer.is_valid():
                    # print(f"Expense item {idx} validation errors:", item_serializer.errors)
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
        # print("Error creating expense:", str(e))
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
def expense_form_view(request):
    cities = City.objects.all()
    items = Item.objects.filter(type_choice='expenses')
    contracts = Contract.objects.all()
    return render(request, 'hygienebox/expense_create.html', {'cities': cities, 'items': items, 'contracts': contracts})

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
        expense = expense.filter(region_id=region)
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
            
            # Parse revenue_items if exists
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
            
            # Manually validate we have revenue items
            if not revenue_items:
                return Response(
                    {'revenue_items': 'This field is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            revenue_data = {
                'city': data.get('city'),
                'region': data.get('region'),
                'districts': data.getlist('districts'),
                'towns': data.getlist('towns'),
                'neighborhoods': data.getlist('neighborhoods'),
            }

            # Create Revenue
            revenue_serializer = RevenueSerializer(data=revenue_data, context={'request': request})
            if not revenue_serializer.is_valid():
                return Response(revenue_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Save normally first
            revenue = revenue_serializer.save()

            # Then update created_by/updated_by
            revenue.save(user=request.user)


            
            # Process each revenue item
            for idx, item_data in enumerate(revenue_items):
                # Handle file upload if specified
                file_key = item_data.get('receipt_file')
                if file_key and file_key in request.FILES:
                    item_data['receipt_file'] = request.FILES[file_key]
                
                # Create revenue item
                item_serializer = RevenueItemSerializer(data=item_data, context={
                    'request': request,
                    'revenue': revenue
                })
                
                if not item_serializer.is_valid():
                    # print(f"Revenue item {idx} validation errors:", item_serializer.errors)
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
    cities = City.objects.all()
    items = Item.objects.filter(type_choice='revenues')
    return render(request, 'hygienebox/revenue_create.html', {'cities': cities, 'items': items})
  
def revenues_list_view(request):
    revenue = Revenue.objects.all().distinct()
    cities = City.objects.all()

    city = request.GET.get('city')
    region = request.GET.get('region')
    district = request.GET.get('district')
    town = request.GET.get('town')
    neighborhood = request.GET.get('neighborhood')

    if city:
        revenue = revenue.filter(city_id=city)
    if region:
        revenue = revenue.filter(region_id=region)
    if district:
        revenue = revenue.filter(districts__id=district)
    if town:
        revenue = revenue.filter(towns__id=town)
    if neighborhood:
        revenue = revenue.filter(neighborhoods__id=neighborhood)

    context = {
        'revenue_list': revenue.distinct(),
        'cities': cities,
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
        district = report_form.cleaned_data.get('district')
        town = report_form.cleaned_data.get('town')
        neighborhood = report_form.cleaned_data.get('neighborhood')
        from_date = report_form.cleaned_data.get('from_date')
        to_date = report_form.cleaned_data.get('to')

        if city:
            filters_revenue &= Q(revenueitem__revenue__city=city)
            filters_expense &= Q(expenseitem__expense__city=city)
        if region:
            filters_revenue &= Q(revenueitem__revenue__region=region)
            filters_expense &= Q(expenseitem__expense__region=region)
        if district:
            filters_revenue &= Q(revenueitem__revenue__districts=district)
            filters_expense &= Q(expenseitem__expense__districts=district)
        if town:
            filters_revenue &= Q(revenueitem__revenue__towns=town)
            filters_expense &= Q(expenseitem__expense__towns=town)
        if neighborhood:
            filters_revenue &= Q(revenueitem__revenue__neighborhoods=neighborhood)
            filters_expense &= Q(expenseitem__expense__neighborhoods=neighborhood)

        if from_date and to_date:
            # 🔥 Here is the corrected line!
            filters_revenue &= Q(revenueitem__distributions__month__range=(from_date, to_date))
            filters_expense &= Q(expenseitem__on_date__range=(from_date, to_date))
        elif from_date:
            filters_revenue &= Q(revenueitem__distributions__month__gte=from_date)
            filters_expense &= Q(expenseitem__on_date__gte=from_date)
        elif to_date:
            filters_revenue &= Q(revenueitem__distributions__month__lte=to_date)
            filters_expense &= Q(expenseitem__on_date__lte=to_date)

    revenues = (
        Item.objects.filter(type_choice="revenues")
        .annotate(
            total_value=Coalesce(Sum('revenueitem__distributions__amount', filter=filters_revenue), Value(0))
        )
        .values('name', 'total_value')
    )

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
