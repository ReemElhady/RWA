from django.http import JsonResponse
from django.shortcuts import render , redirect,get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic.base import View
from django.views.generic.list import ListView
from django.views.generic.edit import DeleteView , CreateView , UpdateView
from core.models import Area , Neighborhood
from .forms import ReportForm, RevenueForm , RevenueItemFormSet , ExpenseForm , ExpenseItemFormSet , ContractForm
from .models import RevenueItem ,ExpenseItem , ExpenseReg , RevenueReg ,Item , Contract
from django.db.models import Sum, Value , Q
from django.db.models.functions import Coalesce
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    total_expense = ExpenseReg.objects.all().aggregate(total=Sum('expense_items__value'))['total'] or 0
    total_revenue = RevenueReg.objects.all().aggregate(total=Sum('revenue_items__value'))['total'] or 0
    
    return render(request , 'hygienebox/dashboard.html',{
                                                        'total_expense':total_expense,
                                                        'total_revenue':total_revenue,
                                                        })

@login_required
def reports(request):
    report_form = ReportForm()
    expense_item_labels = []
    expense_item_values = []
    revenue_item_labels = []
    revenue_item_values = []

    # ✅ Default fetch all data on GET
    if request.method == 'GET':
        expenses = (
            Item.objects.filter(type_choice="expenses")
            .annotate(
                total_value=Coalesce(Sum('expenseitem__value'), Value(0))
            )
            .values('name', 'total_value')
        )

        revenues = (
            Item.objects.filter(type_choice="revenues")
            .annotate(
                total_value=Coalesce(Sum('revenueitem__value'), Value(0))
            )
            .values('name', 'total_value')
        )

    # ✅ Handle POST request (with filtering)
    else:
        report_form = ReportForm(request.POST)
        site_id = request.POST.get('site')
        neighborhood_id = request.POST.get('neighborhood', None)
        from_date = request.POST.get('from_date', None)
        to_date = request.POST.get('to', None)

        # ✅ Build dynamic filtering conditions
        filters_revenue = Q()
        filters_expense = Q()

        # Filter by site
        if site_id:
            site = get_object_or_404(Area, id=int(site_id))
            filters_revenue &= Q(revenueitem__revenue__site=site)
            filters_expense &= Q(expenseitem__expense__site=site)

        # Filter by neighborhood (only if site is provided)
        if neighborhood_id:
            neighborhood = get_object_or_404(Neighborhood, id=int(neighborhood_id))
            filters_revenue &= Q(revenueitem__revenue__neighborhood=neighborhood)
            filters_expense &= Q(expenseitem__expense__neighborhood=neighborhood)

        # ✅ Date range filtering
        if from_date and to_date:
            filters_revenue &= Q(revenueitem__from_date__range=(from_date, to_date))
            filters_expense &= Q(expenseitem__from_date__range=(from_date, to_date))
        elif from_date:
            filters_revenue &= Q(revenueitem__from_date__gte=from_date)
            filters_expense &= Q(expenseitem__from_date__gte=from_date)
        elif to_date:
            filters_revenue &= Q(revenueitem__from_date__lte=to_date)
            filters_expense &= Q(expenseitem__from_date__lte=to_date)

        # ✅ Ensure all items appear, even with 0 values
        revenues = (
            Item.objects.filter(type_choice="revenues")
            .annotate(
                total_value=Coalesce(
                    Sum('revenueitem__value', filter=filters_revenue),
                    Value(0)
                )
            )
            .values('name', 'total_value')
        )

        expenses = (
            Item.objects.filter(type_choice="expenses")
            .annotate(
                total_value=Coalesce(
                    Sum('expenseitem__value', filter=filters_expense),
                    Value(0)
                )
            )
            .values('name', 'total_value')
        )

    # ✅ Populate chart data for both cases
    for item in revenues:
        revenue_item_labels.append(item['name'])
        revenue_item_values.append(item['total_value'])

    for item in expenses:
        expense_item_labels.append(item['name'])
        expense_item_values.append(item['total_value'])

    # ✅ Render template with updated data
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

def load_areas(request):
    areas = Area.objects.all().values('id', 'name')
    return JsonResponse(list(areas), safe=False)

def load_neighborhoods(request):
    area_id = request.GET.get('area_id')
    if area_id:
        neighborhoods = Neighborhood.objects.filter(area_id=area_id).values('id', 'name')
        return JsonResponse(list(neighborhoods), safe=False)
    return JsonResponse({"error": "No area_id provided"}, status=400)

@login_required
def revenue_details(request,pk):
    try:
        revenue = get_object_or_404(RevenueReg,id=pk)
        rev_items = revenue.revenue_items.all()
        data = {
            "register_number": revenue.register_number,
            "site": str(revenue.site),
            "neighborhood": str(revenue.neighborhood) if revenue.neighborhood else "-",
            "total_revenues": revenue.total_revenues,
            "items": [
                {"item_name": item.item.name, "value": item.value,"from":item.from_date,"to":item.to_date} 
                for item in rev_items
            ]
        }
        return JsonResponse(data)
    except RevenueReg.DoesNotExist:
        return JsonResponse({"error": "Revenue not found"}, status=404)

@login_required
def expense_details(request,pk):
    try:
        expense = get_object_or_404(ExpenseReg,id=pk)
        exp_items = expense.expense_items.all()
        data = {
            "register_number": expense.register_number,
            "site": str(expense.site),
            "neighborhood": str(expense.neighborhood) if expense.neighborhood else "-",
            "total_expenses": expense.total_expenses,
            "items": [
                {"item_name": item.item.name, "value": item.value} 
                for item in exp_items
            ]
        }
        return JsonResponse(data)
    except RevenueReg.DoesNotExist:
        return JsonResponse({"error": "Revenue not found"}, status=404)

class RevenueFormView(LoginRequiredMixin,View):
    def get(self, request):
        revenue_form = RevenueForm(prefix='rev')
        formset = RevenueItemFormSet(prefix='rev_item', queryset=RevenueItem.objects.none())
        return render(
            request,
            'hygienebox/revenue_form.html',
            {'revenue_form': revenue_form, 'formset': formset}
        )

    def post(self, request):
        revenue_form = RevenueForm(request.POST, prefix='rev')
        formset = RevenueItemFormSet(request.POST, prefix='rev_item', queryset=RevenueItem.objects.none())

        if revenue_form.is_valid() and formset.is_valid():
            # Save main revenue object
            revenue = revenue_form.save()

            # Save each valid revenue item
            for form in formset:
                if form.has_changed():
                    item = form.save(commit=False)
                    item.revenue = revenue
                    item.save()
            messages.success(request, f"{revenue} Revenue created successfully!")
            return redirect('revenues')

        # Return form with errors and keep data intact
        return render(
            request,
            'hygienebox/revenue_form.html',
            {'revenue_form': revenue_form, 'formset': formset}
        )

class ExpenseFormView(LoginRequiredMixin,View):
    def get(self, request):
        expense_form = ExpenseForm(prefix='exp')
        formset = ExpenseItemFormSet(prefix='exp_item', queryset=ExpenseItem.objects.none())
        return render(
            request,
            'hygienebox/expense_form.html',
            {'expense_form': expense_form, 'formset': formset}
        )

    def post(self, request):
        expense_form = ExpenseForm(request.POST, prefix='exp')
        formset = ExpenseItemFormSet(request.POST, prefix='exp_item', queryset=RevenueItem.objects.none())

        if expense_form.is_valid() and formset.is_valid():
            # Save main expense object
            expense = expense_form.save()

            # Save each valid expense item
            for form in formset:
                if form.has_changed():
                    item = form.save(commit=False)
                    item.expense = expense
                    item.save()
            messages.success(request, f"{expense} Expense created successfully!")
            return redirect('expenses')

        # Return form with errors and keep data intact
        return render(
            request,
            'hygienebox/expense_form.html',
            {'expense_form': expense_form, 'formset': formset}
        )

class RevenueListView(LoginRequiredMixin,ListView):
    model = RevenueReg
    template_name = 'hygienebox/revenue_list.html'
    context_object_name = 'revenues'

    def get_queryset(self):
        # Optimize by prefetching related items
        if self.request.GET.get('site_select') and self.request.GET.get('neighborhood_select'):
            site = get_object_or_404(Area , pk=int(self.request.GET.get('site_select')))
            neighborhood = get_object_or_404(Neighborhood , pk=int(self.request.GET.get('neighborhood_select')))
            return RevenueReg.objects.filter(site=site,neighborhood=neighborhood).prefetch_related('revenue_items')
        if self.request.GET.get('site_select') :
            site = get_object_or_404(Area , pk=int(self.request.GET.get('site_select')))
            return RevenueReg.objects.filter(site=site).prefetch_related('revenue_items')
        return RevenueReg.objects.prefetch_related('revenue_items')

class ExpenseListView(LoginRequiredMixin,ListView):
    model = ExpenseReg
    template_name = 'hygienebox/expense_list.html'
    context_object_name = 'expenses'

    def get_queryset(self):
        # Optimize by prefetching related items
        if self.request.GET.get('site_select') and self.request.GET.get('neighborhood_select'):
            site = get_object_or_404(Area , pk=int(self.request.GET.get('site_select')))
            neighborhood = get_object_or_404(Neighborhood , pk=int(self.request.GET.get('neighborhood_select')))
            return ExpenseReg.objects.filter(site=site,neighborhood=neighborhood).prefetch_related('expense_items')
        if self.request.GET.get('site_select') :
            site = get_object_or_404(Area , pk=int(self.request.GET.get('site_select')))
            return ExpenseReg.objects.filter(site=site).prefetch_related('expense_items')
        return ExpenseReg.objects.prefetch_related('expense_items')

class RevenueEditView(LoginRequiredMixin,View):
    def get(self,request,pk):
        revenue = get_object_or_404(RevenueReg, pk=pk)
        revenue_form = RevenueForm(prefix='rev',instance=revenue)
        formset = RevenueItemFormSet(prefix='rev_item',queryset=RevenueItem.objects.filter(revenue=revenue))
        return render(request, "hygienebox/revenue_edit.html", {
            "revenue_form": revenue_form,
            "items_formset": formset,
            'pk':revenue.register_number
        })

    def post(self, request, pk):
        revenue = get_object_or_404(RevenueReg, pk=pk)
        revenue_form = RevenueForm(request.POST, prefix='rev', instance=revenue)
        formset = RevenueItemFormSet(
            request.POST,
            prefix='rev_item',
            queryset=RevenueItem.objects.filter(revenue=revenue)
        )

        # Debugging: Print errors if forms are invalid
        if not revenue_form.is_valid():
            print("Revenue form errors:", revenue_form.errors)

        if not formset.is_valid():
            print("Formset errors:", formset.errors)

        # Proceed only if both forms are valid
        if revenue_form.is_valid() and formset.is_valid():
            # Save the main revenue form
            revenue = revenue_form.save()

            # Save formset items (new, updated, deleted)
            items = formset.save(commit=False)
            for item in items:
                item.revenue = revenue
                item.save()

            for deleted_item in formset.deleted_objects:
                deleted_item.delete()

            messages.success(request, f"{revenue.register_number} Updated Successfully")
            return redirect("revenues")

        # If the form isn’t valid, re-render with errors
        messages.error(request, "Failed to update. Please check the form data.")
        return render(
            request,
            "hygienebox/revenue_edit.html",
            {
                "revenue_form": revenue_form,
                "items_formset": formset,
                "pk": revenue.register_number,
            },
        )

class ExpenseEditView(LoginRequiredMixin,View):
    def get(self,request,pk):
        expense = get_object_or_404(ExpenseReg, pk=pk)
        expense_form = ExpenseForm(prefix='exp',instance=expense)
        formset = ExpenseItemFormSet(prefix='exp_item',queryset=ExpenseItem.objects.filter(expense=expense))
        return render(request, "hygienebox/expense_edit.html", {
            "expense_form": expense_form,
            "items_formset": formset,
            'pk':expense.register_number
        })

    def post(self, request, pk):
        expense = get_object_or_404(ExpenseReg, pk=pk)
        expense_form = ExpenseForm(request.POST, prefix='exp', instance=expense)
        formset = ExpenseItemFormSet(
            request.POST,
            prefix='exp_item',
            queryset=ExpenseItem.objects.filter(expense=expense),
        )

        # Debugging: Print errors if forms are invalid
        if not expense_form.is_valid():
            print("expense form errors:", expense_form.errors)

        if not formset.is_valid():
            print("Formset errors:", formset.errors)

        # Proceed only if both forms are valid
        if expense_form.is_valid() and formset.is_valid():
            # Save the main expense form
            expense = expense_form.save()

            # Save formset items (new, updated, deleted)
            items = formset.save(commit=False)
            for item in items:
                item.expense = expense
                item.save()

            for deleted_item in formset.deleted_objects:
                deleted_item.delete()

            messages.success(request, f"{expense.register_number} Updated Successfully")
            return redirect("expenses")

        # If the form isn’t valid, re-render with errors
        messages.error(request, "Failed to update. Please check the form data.")
        return render(
            request,
            "hygienebox/expense_edit.html",
            {
                "expense_form": expense_form,
                "items_formset": formset,
                "pk": expense.register_number,
            },
        )

class RevenueDeleteView(LoginRequiredMixin,DeleteView):
    model = RevenueReg
    success_url = reverse_lazy("revenues")
    
class ExpenseDeleteView(LoginRequiredMixin,DeleteView):
    model = ExpenseReg
    success_url = reverse_lazy('expenses')


class ContractListView(LoginRequiredMixin,ListView):
    model = Contract

    def get_queryset(self):
        # Optimize by prefetching related items
        if self.request.GET.get('site_select') and self.request.GET.get('neighborhood_select'):
            site = get_object_or_404(Area , pk=int(self.request.GET.get('site_select')))
            neighborhood = get_object_or_404(Neighborhood , pk=int(self.request.GET.get('neighborhood_select')))
            return Contract.objects.filter(site=site,neighborhood=neighborhood)
        if self.request.GET.get('site_select') :
            site = get_object_or_404(Area , pk=int(self.request.GET.get('site_select')))
            return Contract.objects.filter(site=site)
        return Contract.objects.all()

class ContractDeleteView(LoginRequiredMixin,DeleteView):
    model = Contract
    success_url = reverse_lazy('contracts')

class ContractFormView(LoginRequiredMixin,CreateView):
    model = Contract
    form_class = ContractForm
    template_name = 'hygienebox/contract_form.html'  # For creating new contracts
    success_url = reverse_lazy('contracts')

class ContractEditView(LoginRequiredMixin,UpdateView):
    model = Contract
    form_class = ContractForm
    template_name = 'hygienebox/contract_edit.html'  # For edit contracts
    success_url = reverse_lazy('contracts')