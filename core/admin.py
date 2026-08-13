from django.contrib import admin
from .models import Category, Product, Customer, Supplier, Sale, SaleItem, InventoryMovement

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'quantity', 'selling_price', 'is_active']
    list_filter = ['category', 'is_active', 'supplier']
    search_fields = ['name', 'sku', 'barcode']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'created_at']
    search_fields = ['name', 'email', 'phone']

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'phone', 'email']
    search_fields = ['name', 'contact_person', 'email']

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['invoice_number', 'customer__name']
    readonly_fields = ['created_at']

@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ['sale', 'product', 'quantity', 'price', 'total']
    list_filter = ['sale__status']

@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity', 'movement_type', 'created_at']
    list_filter = ['movement_type']
    readonly_fields = ['created_at']
# core/admin.py - Add these admin classes

from .models import (
    StoreSettings, NotificationSettings, PaymentSettings, 
    DeliverySettings, TaxSettings, SystemSettings, SecuritySettings
)

@admin.register(StoreSettings)
class StoreSettingsAdmin(admin.ModelAdmin):
    list_display = ['store_name', 'store_phone', 'store_email', 'updated_at']
    fieldsets = (
        ('Store Information', {
            'fields': ('store_name', 'store_tagline', 'store_address')
        }),
        ('Contact Information', {
            'fields': ('store_phone', 'store_email')
        }),
        ('Branding', {
            'fields': ('store_logo',)
        }),
    )

@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ['id', 'new_order_alerts', 'low_stock_alerts', 'daily_sales_report', 'updated_at']
    list_filter = ['new_order_alerts', 'low_stock_alerts', 'delivery_updates', 'daily_sales_report']

@admin.register(PaymentSettings)
class PaymentSettingsAdmin(admin.ModelAdmin):
    list_display = ['id', 'cash_enabled', 'card_enabled', 'mobile_money_enabled', 'updated_at']
    list_filter = ['cash_enabled', 'card_enabled', 'mobile_money_enabled']

@admin.register(DeliverySettings)
class DeliverySettingsAdmin(admin.ModelAdmin):
    list_display = ['id', 'delivery_enabled', 'delivery_fee', 'free_delivery_threshold', 'updated_at']

@admin.register(TaxSettings)
class TaxSettingsAdmin(admin.ModelAdmin):
    list_display = ['id', 'tax_rate', 'default_discount', 'updated_at']

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ['id', 'currency', 'date_format', 'timezone', 'language', 'maintenance_mode']

@admin.register(SecuritySettings)
class SecuritySettingsAdmin(admin.ModelAdmin):
    list_display = ['id', 'session_timeout', 'two_factor_auth', 'updated_at']