from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # POS
    path('pos/', views.pos_view, name='pos'),
    path('pos/add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('pos/remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    path('pos/update-cart-item/', views.update_cart_item, name='update_cart_item'),
    path('pos/clear-cart/', views.clear_cart, name='clear_cart'),
    path('pos/process-payment/', views.process_payment, name='process_payment'),
    
    # Products
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_create, name='product_create'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    
    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_create, name='category_create'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    
    # Customers
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.customer_create, name='customer_create'),
    path('customers/<int:pk>/edit/', views.customer_edit, name='customer_edit'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='customer_delete'),
    
    # Suppliers
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.supplier_create, name='supplier_create'),
    path('suppliers/<int:pk>/edit/', views.supplier_edit, name='supplier_edit'),
    path('suppliers/<int:pk>/delete/', views.supplier_delete, name='supplier_delete'),
    
    # Sales
    path('sales/', views.sale_list, name='sale_list'),
    path('sales/<int:pk>/', views.sale_detail, name='sale_detail'),
    path('sales/<int:pk>/void/', views.sale_void, name='sale_void'),
    
    # Reports
    path('reports/inventory/', views.inventory_report, name='inventory_report'),
    path('reports/sales/', views.sales_report, name='sales_report'),
    path('sales/<int:pk>/update-status/', views.update_order_status, name='update_order_status'),
    path('sales/export/', views.export_orders_csv, name='export_orders'),
    path('settings/', views.settings_view, name='settings'),
    path('settings/store/', views.update_store_settings, name='update_store_settings'),
    path('settings/notifications/', views.update_notification_settings, name='update_notification_settings'),
    path('settings/payments/', views.update_payment_settings, name='update_payment_settings'),
    path('settings/delivery/', views.update_delivery_settings, name='update_delivery_settings'),
    path('settings/tax/', views.update_tax_settings, name='update_tax_settings'),
    path('settings/system/', views.update_system_settings, name='update_system_settings'),
    path('settings/security/', views.update_security_settings, name='update_security_settings'),
    path('settings/export/', views.export_settings, name='export_settings'),
    path('settings/import/', views.import_settings, name='import_settings'),
    ]