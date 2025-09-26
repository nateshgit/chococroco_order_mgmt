from django.urls import path
from . import views

urlpatterns = [
    # Orders section
    # path('orders/', views.order_list, name='order_list'),
    # path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    # path('orders/<int:pk>/invoice/', views.generate_invoice, name='generate_invoice'),

    # Reports section
    path('reports/', views.order_report, name='order_report'),
    # path('reports/export/', views.export_orders_csv, name='export_orders_csv'),
]
