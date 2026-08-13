from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

class Supplier(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    sku = models.CharField(max_length=50, unique=True)
    barcode = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity = models.IntegerField(default=0)
    reorder_level = models.IntegerField(default=10)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.sku}"

class Customer(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# core/models.py - Update the Sale model

class Sale(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('mobile', 'Mobile Money'),
    ]

    # Updated Status Choices with Delivery States
    STATUS_CHOICES = [
        ('pending', '🔄 Pending'),
        ('processing', '📦 Processing'),
        ('shipped', '🚚 Shipped'),
        ('out_for_delivery', '🚛 Out for Delivery'),
        ('delivered', '✅ Delivered'),
        ('cancelled', '❌ Cancelled'),
    ]

    invoice_number = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Delivery Information
    delivery_address = models.TextField(blank=True)
    delivery_date = models.DateTimeField(null=True, blank=True)
    tracking_number = models.CharField(max_length=50, blank=True)
    courier_name = models.CharField(max_length=100, blank=True)
    delivery_notes = models.TextField(blank=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.get_status_display()}"

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

class InventoryMovement(models.Model):
    MOVEMENT_TYPES = [
        ('purchase', 'Purchase'),
        ('sale', 'Sale'),
        ('return', 'Return'),
        ('adjustment', 'Adjustment'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements')
    quantity = models.IntegerField()
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    reference = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name} - {self.movement_type}"
# core/models.py - Add these models

class StoreSettings(models.Model):
    """Store configuration settings"""
    store_name = models.CharField(max_length=200, default="Vera's Choice")
    store_tagline = models.CharField(max_length=500, blank=True, default="Royal Boutique POS System")
    store_address = models.TextField(blank=True, default="123 Royal Street, Boutique District, City")
    store_phone = models.CharField(max_length=20, blank=True, default="+1 234 567 8900")
    store_email = models.EmailField(blank=True, default="info@veraschoice.com")
    store_logo = models.ImageField(upload_to='store_logos/', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.store_name

    class Meta:
        verbose_name = "Store Setting"
        verbose_name_plural = "Store Settings"

class NotificationSettings(models.Model):
    """Notification preferences"""
    new_order_alerts = models.BooleanField(default=True)
    low_stock_alerts = models.BooleanField(default=True)
    delivery_updates = models.BooleanField(default=False)
    daily_sales_report = models.BooleanField(default=True)
    security_alerts = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Notification Settings"

    class Meta:
        verbose_name = "Notification Setting"
        verbose_name_plural = "Notification Settings"

class PaymentSettings(models.Model):
    """Payment method configurations"""
    cash_enabled = models.BooleanField(default=True)
    card_enabled = models.BooleanField(default=True)
    mobile_money_enabled = models.BooleanField(default=False)
    crypto_enabled = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Payment Settings"

    class Meta:
        verbose_name = "Payment Setting"
        verbose_name_plural = "Payment Settings"

class DeliverySettings(models.Model):
    """Delivery configuration"""
    delivery_enabled = models.BooleanField(default=True)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=5.00)
    free_delivery_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)
    delivery_days = models.CharField(max_length=100, default="2-5 business days")
    courier_partners = models.CharField(max_length=500, blank=True, default="DHL, FedEx, UPS")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Delivery Settings"

    class Meta:
        verbose_name = "Delivery Setting"
        verbose_name_plural = "Delivery Settings"

class TaxSettings(models.Model):
    """Tax and discount configuration"""
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    default_discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    discount_rules = models.TextField(blank=True, default="""• 10% off on orders above $100
• Loyalty points redemption
• Seasonal promotions
• First-time customer discount: 15%""")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Tax Settings"

    class Meta:
        verbose_name = "Tax Setting"
        verbose_name_plural = "Tax Settings"

class SystemSettings(models.Model):
    """System configuration"""
    CURRENCY_CHOICES = [
        ('USD', 'USD ($)'),
        ('EUR', 'EUR (€)'),
        ('GBP', 'GBP (£)'),
        ('INR', 'INR (₹)'),
    ]
    DATE_FORMAT_CHOICES = [
        ('MM/DD/YYYY', 'MM/DD/YYYY'),
        ('DD/MM/YYYY', 'DD/MM/YYYY'),
        ('YYYY-MM-DD', 'YYYY-MM-DD'),
    ]
    TIMEZONE_CHOICES = [
        ('UTC', 'UTC'),
        ('EST', 'EST'),
        ('PST', 'PST'),
        ('GMT', 'GMT'),
    ]
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
    ]

    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default='USD')
    date_format = models.CharField(max_length=20, choices=DATE_FORMAT_CHOICES, default='MM/DD/YYYY')
    timezone = models.CharField(max_length=10, choices=TIMEZONE_CHOICES, default='GMT')
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en')
    maintenance_mode = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "System Settings"

    class Meta:
        verbose_name = "System Setting"
        verbose_name_plural = "System Settings"

class SecuritySettings(models.Model):
    """Security configuration"""
    session_timeout = models.IntegerField(default=60, help_text="Minutes")
    two_factor_auth = models.BooleanField(default=False)
    password_min_length = models.BooleanField(default=True)
    password_case_required = models.BooleanField(default=True)
    password_special_chars = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Security Settings"

    class Meta:
        verbose_name = "Security Setting"
        verbose_name_plural = "Security Settings"