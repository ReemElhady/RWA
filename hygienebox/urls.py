from django.urls import path
from . import views
urlpatterns = [
    path('dashboard/',views.dashboard,name='hygienebox_dashboard'),
    path('reports/',views.reports,name='reports'),
    path('sites/',views.load_areas,name='sites'),
    path('neighborhoods/',views.load_neighborhoods,name='neighborhoods'),
    path('create/revenue',views.RevenueFormView.as_view(),name='create_revenue'),
    path('create/expense',views.ExpenseFormView.as_view(),name='create_expense'),
    path('revenues',views.RevenueListView.as_view(),name='revenues'),
    path('expenses',views.ExpenseListView.as_view(),name='expenses'),
    path('revenue/details/<int:pk>/',views.revenue_details,name='rev-details'),
    path('expense/details/<int:pk>/',views.expense_details,name='exp-details'),
    path('revenue/edit/<int:pk>/',views.RevenueEditView.as_view(),name='edit-revenue'),
    path('expense/edit/<int:pk>/',views.ExpenseEditView.as_view(),name='edit-expense'),
    path('revenue/delete/<int:pk>/',views.RevenueDeleteView.as_view(),name='delete-revenue'),
    path('expense/delete/<int:pk>/',views.ExpenseDeleteView.as_view(),name='delete-expense'),
    path('contracts/',views.ContractListView.as_view(),name='contracts'),
    path('create/contract/',views.ContractFormView.as_view(),name='create_contract'),
    path('edit/contract/<int:pk>/',views.ContractEditView.as_view(),name='edit-contract'),
    path('delete/contract/<int:pk>/',views.ContractDeleteView.as_view(),name='delete-contract'),
]