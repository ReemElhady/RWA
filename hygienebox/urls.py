from django.urls import path
from . import views
urlpatterns = [
    path('dashboard/',views.dashboard,name='hygienebox_dashboard'),
    
    #Contracts
    path('contracts/create/', views.create_contract, name='create_contract'),
    path('contracts/form/', views.contract_form_view, name='contract-form'),
    path('contracts/<int:contract_id>/committed-areas/', views.get_committed_areas, name='committed-areas'),
    path('regions/', views.get_regions),
    path('districts/', views.get_districts),
    path('towns/', views.get_towns),
    path('neighborhoods/', views.get_neighborhoods),
    path('contracts/', views.contract_list_view, name='contracts'),
    path('contracts/edit/<int:contract_id>/', views.edit_contract, name='edit-contract'),
    path('contracts/delete/<int:contract_id>/', views.delete_contract, name='delete-contract'),
    path('contracts/<int:contract_id>/analytics/', views.contract_analytics_view, name='contract-analytics'),
    
    #Expenses
    path('create/expense/', views.create_expense, name='create_expense'),
    path('expense/form/', views.expense_form_view, name='expense-form'),
    path('expenses/list/',views.expense_list_view,name='expenses_list'),
    path('expenses/delete/<int:expense_id>/', views.delete_expense, name='delete-expense'),
    path('expenses/edit/<int:expense_id>/', views.edit_expense, name='edit-expense'),
    
    
    #Revenues
    path('create/revenue/', views.create_revenue, name='create_revenue'),
    path('revenue/form/', views.revenue_form_view, name='revenue-form'),
    path('revenues/list/',views.revenues_list_view,name='revenues_list'),
    path('revenues/delete/<int:revenue_id>/', views.delete_revenue, name='delete-revenue'),
    path('revenues/edit/<int:revenue_id>/', views.edit_revenue, name='edit-revenue'),
    
    #Reports
    path('reports/',views.reports,name='reports'),
]