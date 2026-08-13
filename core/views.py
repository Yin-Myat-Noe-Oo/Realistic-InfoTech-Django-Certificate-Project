from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.db.models import Sum, Count, Q, F, Value
from django.db.models.functions import Coalesce, TruncDate
from django.db.models import DecimalField
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from decimal import Decimal
import json
from datetime import datetime, timedelta
import csv
import os

from .models import (
    Product, Category, Sale, SaleItem, Customer, Supplier, InventoryMovement,
    StoreSettings, NotificationSettings, PaymentSettings, 
    DeliverySettings, TaxSettings, SystemSettings, SecuritySettings
)
from .forms import (
    ProductForm, CategoryForm, CustomerForm, SaleForm, SupplierForm
)

# ========== SETTINGS HELPERS ==========

def get_store_settings():
    """Get or create store settings"""
    settings, _ = StoreSettings.objects.get_or_create(id=1)
    return settings

def get_payment_settings():
    """Get or create payment settings"""
    settings, _ = PaymentSettings.objects.get_or_create(id=1)
    return settings

def get_tax_settings():
    """Get or create tax settings"""
    settings, _ = TaxSettings.objects.get_or_create(id=1)
    return settings

def get_system_settings():
    """Get or create system settings"""
    settings, _ = SystemSettings.objects.get_or_create(id=1)
    return settings

def get_delivery_settings():
    """Get or create delivery settings"""
    settings, _ = DeliverySettings.objects.get_or_create(id=1)
    return settings

# ========== AUTHENTICATION VIEWS ==========

def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}! 👑')
                return redirect('core:dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {'form': form})

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Account created successfully! Welcome {user.username}! 👑')
            return redirect('core:dashboard')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = UserCreationForm()
    
    return render(request, 'signup.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out. 👋')
    return redirect('core:login')

# ========== DASHBOARD ==========

@login_required
def dashboard(request):
    total_products = Product.objects.count()
    low_stock = Product.objects.filter(quantity__lte=F('reorder_level'), is_active=True)
    total_customers = Customer.objects.count()
    
    today = timezone.now().date()
    today_sales = Sale.objects.filter(created_at__date=today, status='completed')
    total_sales_today = today_sales.aggregate(total=Sum('total_amount'))['total'] or 0
    
    recent_sales = Sale.objects.filter(status='completed').order_by('-created_at')[:10]
    
    # Get store settings for display
    store_settings = get_store_settings()
    
    context = {
        'total_products': total_products,
        'low_stock_count': low_stock.count(),
        'low_stock_products': low_stock[:5],
        'total_customers': total_customers,
        'total_sales_today': total_sales_today,
        'recent_sales': recent_sales,
        'store_settings': store_settings,
    }
    return render(request, 'dashboard.html', context)

# ========== POS ==========

@login_required
def pos_view(request):
    products = Product.objects.filter(is_active=True, quantity__gt=0)
    categories = Category.objects.all()
    customers = Customer.objects.all()
    cart = request.session.get('cart', [])
    
    # Get payment settings to show only enabled payment methods
    payment_settings = get_payment_settings()
    
    # Build payment method options based on settings
    payment_methods = []
    if payment_settings.cash_enabled:
        payment_methods.append(('cash', 'Cash'))
    if payment_settings.card_enabled:
        payment_methods.append(('card', 'Card'))
    if payment_settings.mobile_money_enabled:
        payment_methods.append(('mobile', 'Mobile Money'))
    
    # Get store settings
    store_settings = get_store_settings()
    tax_settings = get_tax_settings()
    
    context = {
        'products': products,
        'categories': categories,
        'customers': customers,
        'cart': cart,
        'payment_methods': payment_methods,
        'store_settings': store_settings,
        'tax_rate': tax_settings.tax_rate,
    }
    return render(request, 'pos.html', context)

@login_required
def add_to_cart(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        
        try:
            product = Product.objects.get(id=product_id)
            cart = request.session.get('cart', [])
            
            for item in cart:
                if item['product_id'] == product_id:
                    item['quantity'] += quantity
                    item['total'] = float(item['quantity'] * float(item['price']))
                    request.session['cart'] = cart
                    return JsonResponse({'success': True})
            
            cart.append({
                'product_id': product_id,
                'name': product.name,
                'price': float(product.selling_price),
                'quantity': quantity,
                'total': float(quantity * float(product.selling_price)),
                'stock': product.quantity
            })
            
            request.session['cart'] = cart
            return JsonResponse({'success': True})
            
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Product not found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def remove_from_cart(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        cart = request.session.get('cart', [])
        cart = [item for item in cart if item['product_id'] != product_id]
        request.session['cart'] = cart
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})

@login_required
def update_cart_item(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        cart = request.session.get('cart', [])
        
        for item in cart:
            if item['product_id'] == product_id:
                if quantity <= 0:
                    cart.remove(item)
                else:
                    item['quantity'] = quantity
                    item['total'] = float(quantity * float(item['price']))
                break
        
        request.session['cart'] = cart
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})

@login_required
def clear_cart(request):
    if request.method == 'POST':
        request.session['cart'] = []
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required
def process_payment(request):
    if request.method == 'POST':
        cart = request.session.get('cart', [])
        
        if not cart:
            messages.error(request, 'Cart is empty!')
            return redirect('core:pos')
        
        # Get settings
        payment_settings = get_payment_settings()
        tax_settings = get_tax_settings()
        delivery_settings = get_delivery_settings()
        
        # Check if payment method is enabled
        payment_method = request.POST.get('payment_method', 'cash')
        is_valid_payment = False
        
        if payment_method == 'cash' and payment_settings.cash_enabled:
            is_valid_payment = True
        elif payment_method == 'card' and payment_settings.card_enabled:
            is_valid_payment = True
        elif payment_method == 'mobile' and payment_settings.mobile_money_enabled:
            is_valid_payment = True
        
        if not is_valid_payment:
            messages.error(request, 'This payment method is not enabled!')
            return redirect('core:pos')
        
        # Calculate totals with tax settings
        subtotal = Decimal(str(sum(item['total'] for item in cart)))
        discount = Decimal(request.POST.get('discount', '0'))
        
        # Use tax rate from settings
        tax_rate = tax_settings.tax_rate / Decimal('100')
        tax = (subtotal - discount) * tax_rate
        total = subtotal - discount + tax
        
        # Add delivery fee if enabled and order is below threshold
        delivery_fee = Decimal('0')
        if delivery_settings.delivery_enabled:
            if total < delivery_settings.free_delivery_threshold:
                delivery_fee = delivery_settings.delivery_fee
                total += delivery_fee
        
        # Generate invoice number
        today = datetime.now().strftime('%Y%m%d')
        count = Sale.objects.filter(created_at__date=timezone.now().date()).count() + 1
        invoice_number = f"INV-{today}-{count:04d}"
        
        sale = Sale.objects.create(
            invoice_number=invoice_number,
            customer_id=request.POST.get('customer_id') or None,
            user=request.user,
            subtotal=subtotal,
            discount=discount,
            tax=tax,
            total_amount=total,
            payment_method=payment_method,
            status='completed',
            notes=request.POST.get('notes', ''),
            delivery_address=request.POST.get('delivery_address', ''),
        )
        
        for item in cart:
            product = Product.objects.get(id=item['product_id'])
            
            SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=item['quantity'],
                price=Decimal(str(item['price'])),
                total=Decimal(str(item['total']))
            )
            
            product.quantity -= item['quantity']
            product.save()
            
            InventoryMovement.objects.create(
                product=product,
                quantity=-item['quantity'],
                movement_type='sale',
                reference=sale.invoice_number,
                notes=f'Sale #{sale.invoice_number}',
                created_by=request.user
            )
        
        request.session['cart'] = []
        messages.success(request, f'Sale {sale.invoice_number} completed!')
        return redirect('core:sale_detail', pk=sale.pk)
    
    return redirect('core:pos')

# ========== PRODUCT CRUD ==========

@login_required
def product_list(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    
    search_query = request.GET.get('search')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(sku__icontains=search_query)
        )
    
    context = {
        'products': products,
        'categories': categories,
        'selected_category': int(category_id) if category_id else 0,
        'search_query': search_query,
    }
    return render(request, 'product_list.html', context)

@login_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product {product.name} created!')
            return redirect('core:product_list')
    else:
        form = ProductForm()
    
    return render(request, 'product_form.html', {'form': form, 'title': 'Add Product'})

@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'Product {product.name} updated!')
            return redirect('core:product_list')
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'product_form.html', {'form': form, 'title': 'Edit Product'})

@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product {product_name} deleted!')
        return redirect('core:product_list')
    
    return render(request, 'confirm_delete.html', {'object': product, 'type': 'Product'})

# ========== CATEGORY CRUD ==========

@login_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'category_list.html', {'categories': categories})

@login_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category {category.name} created!')
            return redirect('core:category_list')
    else:
        form = CategoryForm()
    
    return render(request, 'category_form.html', {'form': form, 'title': 'Add Category'})

@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category_name = category.name
        category.delete()
        messages.success(request, f'Category {category_name} deleted!')
        return redirect('core:category_list')
    
    return render(request, 'confirm_delete.html', {'object': category, 'type': 'Category'})

# ========== CUSTOMER CRUD ==========

@login_required
def customer_list(request):
    customers = Customer.objects.all()
    search_query = request.GET.get('search')
    if search_query:
        customers = customers.filter(
            Q(name__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    return render(request, 'customer_list.html', {'customers': customers, 'search_query': search_query})

@login_required
def customer_create(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f'Customer {customer.name} added!')
            return redirect('core:customer_list')
    else:
        form = CustomerForm()
    
    return render(request, 'customer_form.html', {'form': form, 'title': 'Add Customer'})

@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, f'Customer {customer.name} updated!')
            return redirect('core:customer_list')
    else:
        form = CustomerForm(instance=customer)
    
    return render(request, 'customer_form.html', {'form': form, 'title': 'Edit Customer'})

@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer_name = customer.name
        customer.delete()
        messages.success(request, f'Customer {customer_name} deleted!')
        return redirect('core:customer_list')
    
    return render(request, 'confirm_delete.html', {'object': customer, 'type': 'Customer'})

# ========== SUPPLIER CRUD ==========

@login_required
def supplier_list(request):
    suppliers = Supplier.objects.all()
    search_query = request.GET.get('search')
    if search_query:
        suppliers = suppliers.filter(
            Q(name__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    return render(request, 'supplier_list.html', {'suppliers': suppliers, 'search_query': search_query})

@login_required
def supplier_create(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            messages.success(request, f'Supplier {supplier.name} added!')
            return redirect('core:supplier_list')
    else:
        form = SupplierForm()
    
    return render(request, 'supplier_form.html', {'form': form, 'title': 'Add Supplier'})

@login_required
def supplier_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, f'Supplier {supplier.name} updated!')
            return redirect('core:supplier_list')
    else:
        form = SupplierForm(instance=supplier)
    
    return render(request, 'supplier_form.html', {'form': form, 'title': 'Edit Supplier'})

@login_required
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier_name = supplier.name
        supplier.delete()
        messages.success(request, f'Supplier {supplier_name} deleted!')
        return redirect('core:supplier_list')
    
    return render(request, 'confirm_delete.html', {'object': supplier, 'type': 'Supplier'})

# ========== SALES ==========

@login_required
def sale_list(request):
    sales = Sale.objects.all()
    status = request.GET.get('status')
    if status:
        sales = sales.filter(status=status)
    
    search = request.GET.get('search')
    if search:
        sales = sales.filter(invoice_number__icontains=search)
    
    # Stats for dashboard
    total_orders = Sale.objects.count()
    pending_orders = Sale.objects.filter(status='pending').count()
    shipping_orders = Sale.objects.filter(status__in=['processing', 'shipped', 'out_for_delivery']).count()
    delivered_orders = Sale.objects.filter(status='delivered').count()
    
    context = {
        'sales': sales,
        'statuses': Sale.STATUS_CHOICES,
        'selected_status': status,
        'search': search,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'shipping_orders': shipping_orders,
        'delivered_orders': delivered_orders,
    }
    return render(request, 'sale_list.html', context)

@login_required
def sale_detail(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    return render(request, 'sale_detail.html', {'sale': sale})

@login_required
def sale_void(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        if sale.status == 'completed':
            for item in sale.items.all():
                product = item.product
                product.quantity += item.quantity
                product.save()
                
                InventoryMovement.objects.create(
                    product=product,
                    quantity=item.quantity,
                    movement_type='return',
                    reference=sale.invoice_number,
                    notes=f'Void sale #{sale.invoice_number}',
                    created_by=request.user
                )
            
            sale.status = 'cancelled'
            sale.save()
            messages.success(request, f'Sale {sale.invoice_number} voided.')
        else:
            messages.error(request, 'Only completed sales can be voided.')
        
        return redirect('core:sale_detail', pk=sale.pk)
    
    return render(request, 'confirm_delete.html', {'object': sale, 'type': 'Sale'})

@login_required
def update_order_status(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        tracking_number = request.POST.get('tracking_number', '')
        courier_name = request.POST.get('courier_name', '')
        delivery_notes = request.POST.get('delivery_notes', '')
        
        if status in dict(Sale.STATUS_CHOICES):
            sale.status = status
            sale.tracking_number = tracking_number
            sale.courier_name = courier_name
            sale.delivery_notes = delivery_notes
            
            # Set delivery date when status changes to delivered
            if status == 'delivered' and not sale.delivery_date:
                sale.delivery_date = timezone.now()
            
            sale.save()
            
            # Add status change message
            status_display = dict(Sale.STATUS_CHOICES)[status]
            messages.success(request, f'Order {sale.invoice_number} status updated to: {status_display}')
            
        return redirect('core:sale_detail', pk=sale.pk)
    
    return redirect('core:sale_detail', pk=sale.pk)

# ========== REPORTS ==========
@login_required
def inventory_report(request):
    # Start with all products
    products = Product.objects.all()
    
    # Get filter parameters from GET request
    category_id = request.GET.get('category')
    stock_status = request.GET.get('stock_status')
    
    # Apply category filter
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Apply stock status filter
    if stock_status == 'low':
        products = products.filter(quantity__lte=F('reorder_level'), is_active=True)
    elif stock_status == 'out':
        products = products.filter(quantity=0, is_active=True)
    elif stock_status == 'in':
        products = products.filter(quantity__gt=0, is_active=True)
    
    # Calculate statistics on filtered products
    total_items = products.count()
    
    total_value = products.aggregate(
        total=Coalesce(
            Sum(F('quantity') * F('purchase_price'), output_field=DecimalField()),
            Value(0, output_field=DecimalField())
        )
    )['total']
    
    # Low stock count (global, not filtered)
    low_stock = Product.objects.filter(quantity__lte=F('reorder_level'), is_active=True)
    
    context = {
        'products': products,
        'total_items': total_items,
        'total_value': total_value or 0,
        'low_stock_count': low_stock.count(),
        'low_stock_products': low_stock,
        'categories': Category.objects.all(),
        'selected_category': int(category_id) if category_id else '',
        'stock_status': stock_status or '',
    }
    return render(request, 'inventory_report.html', context)
@login_required
def sales_report(request):
    today = timezone.now().date()
    date_from = request.GET.get('date_from', today.replace(day=1).isoformat())
    date_to = request.GET.get('date_to', today.isoformat())
    
    sales = Sale.objects.filter(
        status='completed',
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    )
    
    total_sales = sales.count()
    total_revenue = sales.aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Using TruncDate for cleaner date grouping
    daily_sales = sales.annotate(
        sale_date=TruncDate('created_at')
    ).values('sale_date').annotate(
        daily_total=Sum('total_amount'),
        daily_count=Count('id')
    ).order_by('sale_date')
    
    # Convert to list with proper date formatting
    daily_sales_list = []
    for day in daily_sales:
        daily_sales_list.append({
            'date': day['sale_date'],
            'total': day['daily_total'] or 0,
            'count': day['daily_count'] or 0
        })
    
    context = {
        'date_from': date_from,
        'date_to': date_to,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'daily_sales': daily_sales_list,
        'sales': sales[:20],
    }
    return render(request, 'sales_report.html', context)

# ========== EXPORT ORDERS CSV ==========

@login_required
def export_orders_csv(request):
    """Export filtered orders as CSV file"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders_export.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Invoice', 'Customer', 'Email', 'Phone', 'Date', 'Items',
        'Subtotal', 'Discount', 'Tax', 'Total', 'Payment', 'Status',
        'Tracking', 'Courier', 'Delivery Address'
    ])
    
    # Get filtered orders
    orders = Sale.objects.all().order_by('-created_at')
    
    # Apply filters if provided
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    
    search = request.GET.get('search')
    if search:
        orders = orders.filter(
            Q(invoice_number__icontains=search) |
            Q(customer__name__icontains=search)
        )
    
    date_from = request.GET.get('date_from')
    if date_from:
        orders = orders.filter(created_at__date__gte=date_from)
    
    # Write data
    for order in orders:
        writer.writerow([
            order.invoice_number,
            order.customer.name if order.customer else 'Walk-in',
            order.customer.email if order.customer else '',
            order.customer.phone if order.customer else '',
            order.created_at.strftime('%Y-%m-%d %H:%M'),
            order.items.count(),
            order.subtotal,
            order.discount,
            order.tax,
            order.total_amount,
            order.get_payment_method_display(),
            order.get_status_display(),
            order.tracking_number or '',
            order.courier_name or '',
            order.delivery_address or ''
        ])
    
    return response

# ========== SETTINGS VIEWS ==========

@login_required
def settings_view(request):
    """Main settings page - gets or creates all settings"""
    # Get or create each setting
    store_settings, _ = StoreSettings.objects.get_or_create(id=1)
    notification_settings, _ = NotificationSettings.objects.get_or_create(id=1)
    payment_settings, _ = PaymentSettings.objects.get_or_create(id=1)
    delivery_settings, _ = DeliverySettings.objects.get_or_create(id=1)
    tax_settings, _ = TaxSettings.objects.get_or_create(id=1)
    system_settings, _ = SystemSettings.objects.get_or_create(id=1)
    security_settings, _ = SecuritySettings.objects.get_or_create(id=1)
    
    context = {
        'title': 'Settings',
        'store_settings': store_settings,
        'notification_settings': notification_settings,
        'payment_settings': payment_settings,
        'delivery_settings': delivery_settings,
        'tax_settings': tax_settings,
        'system_settings': system_settings,
        'security_settings': security_settings,
    }
    return render(request, 'settings.html', context)

@login_required
def update_store_settings(request):
    """Update store settings"""
    if request.method == 'POST':
        store, _ = StoreSettings.objects.get_or_create(id=1)
        
        store.store_name = request.POST.get('store_name', store.store_name)
        store.store_tagline = request.POST.get('store_tagline', store.store_tagline)
        store.store_address = request.POST.get('store_address', store.store_address)
        store.store_phone = request.POST.get('store_phone', store.store_phone)
        store.store_email = request.POST.get('store_email', store.store_email)
        
        # Handle logo upload
        if 'store_logo' in request.FILES:
            logo_file = request.FILES['store_logo']
            # Delete old logo if exists
            if store.store_logo and os.path.isfile(store.store_logo.path):
                os.remove(store.store_logo.path)
            store.store_logo.save(logo_file.name, logo_file)
        
        store.save()
        messages.success(request, 'Store settings updated successfully! 🏪')
        return redirect('core:settings')
    
    return redirect('core:settings')

@login_required
def update_notification_settings(request):
    """Update notification settings"""
    if request.method == 'POST':
        notifications, _ = NotificationSettings.objects.get_or_create(id=1)
        
        notifications.new_order_alerts = 'new_order_alerts' in request.POST
        notifications.low_stock_alerts = 'low_stock_alerts' in request.POST
        notifications.delivery_updates = 'delivery_updates' in request.POST
        notifications.daily_sales_report = 'daily_sales_report' in request.POST
        notifications.security_alerts = 'security_alerts' in request.POST
        
        notifications.save()
        messages.success(request, 'Notification settings updated successfully! 🔔')
        return redirect('core:settings')
    
    return redirect('core:settings')

@login_required
def update_payment_settings(request):
    """Update payment settings - affects POS payment options"""
    if request.method == 'POST':
        payments, _ = PaymentSettings.objects.get_or_create(id=1)
        
        payments.cash_enabled = 'cash_enabled' in request.POST
        payments.card_enabled = 'card_enabled' in request.POST
        payments.mobile_money_enabled = 'mobile_money_enabled' in request.POST
        payments.crypto_enabled = 'crypto_enabled' in request.POST
        
        payments.save()
        messages.success(request, 'Payment settings updated successfully! 💳')
        return redirect('core:settings')
    
    return redirect('core:settings')

@login_required
def update_delivery_settings(request):
    """Update delivery settings"""
    if request.method == 'POST':
        delivery, _ = DeliverySettings.objects.get_or_create(id=1)
        
        delivery.delivery_enabled = 'delivery_enabled' in request.POST
        delivery.delivery_fee = request.POST.get('delivery_fee', delivery.delivery_fee)
        delivery.free_delivery_threshold = request.POST.get('free_delivery_threshold', delivery.free_delivery_threshold)
        delivery.delivery_days = request.POST.get('delivery_days', delivery.delivery_days)
        delivery.courier_partners = request.POST.get('couriers', delivery.courier_partners)
        
        delivery.save()
        messages.success(request, 'Delivery settings updated successfully! 🚚')
        return redirect('core:settings')
    
    return redirect('core:settings')

@login_required
def update_tax_settings(request):
    """Update tax settings - affects POS calculations"""
    if request.method == 'POST':
        tax, _ = TaxSettings.objects.get_or_create(id=1)
        
        tax.tax_rate = request.POST.get('tax_rate', tax.tax_rate)
        tax.default_discount = request.POST.get('default_discount', tax.default_discount)
        tax.discount_rules = request.POST.get('discount_rules', tax.discount_rules)
        
        tax.save()
        messages.success(request, 'Tax settings updated successfully! 📊')
        return redirect('core:settings')
    
    return redirect('core:settings')

@login_required
def update_system_settings(request):
    """Update system settings"""
    if request.method == 'POST':
        system, _ = SystemSettings.objects.get_or_create(id=1)
        
        system.currency = request.POST.get('currency', system.currency)
        system.date_format = request.POST.get('date_format', system.date_format)
        system.timezone = request.POST.get('timezone', system.timezone)
        system.language = request.POST.get('language', system.language)
        system.maintenance_mode = 'maintenance_mode' in request.POST
        
        system.save()
        messages.success(request, 'System settings updated successfully! ⚙️')
        return redirect('core:settings')
    
    return redirect('core:settings')

@login_required
def update_security_settings(request):
    """Update security settings"""
    if request.method == 'POST':
        security, _ = SecuritySettings.objects.get_or_create(id=1)
        
        security.session_timeout = request.POST.get('session_timeout', security.session_timeout)
        security.two_factor_auth = 'two_factor_auth' in request.POST
        security.password_min_length = 'password_min_length' in request.POST
        security.password_case_required = 'password_case_required' in request.POST
        security.password_special_chars = 'password_special_chars' in request.POST
        
        security.save()
        messages.success(request, 'Security settings updated successfully! 🔒')
        return redirect('core:settings')
    
    return redirect('core:settings')

@login_required
def export_settings(request):
    """Export all settings as JSON"""
    data = {
        'store': StoreSettings.objects.first(),
        'notifications': NotificationSettings.objects.first(),
        'payments': PaymentSettings.objects.first(),
        'delivery': DeliverySettings.objects.first(),
        'tax': TaxSettings.objects.first(),
        'system': SystemSettings.objects.first(),
        'security': SecuritySettings.objects.first(),
    }
    
    # Convert to JSON
    json_data = {}
    for key, value in data.items():
        if value:
            json_data[key] = {
                'id': value.id,
                'fields': {}
            }
            for field in value._meta.fields:
                field_value = getattr(value, field.name)
                if hasattr(field_value, 'strftime'):
                    field_value = field_value.strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(field_value, Decimal):
                    field_value = str(field_value)
                json_data[key]['fields'][field.name] = str(field_value)
    
    response = JsonResponse(json_data, json_dumps_params={'indent': 2})
    response['Content-Disposition'] = 'attachment; filename="settings_backup.json"'
    return response

@login_required
def import_settings(request):
    """Import settings from JSON backup"""
    if request.method == 'POST' and request.FILES.get('import_file'):
        try:
            file = request.FILES['import_file']
            data = json.loads(file.read().decode('utf-8'))
            
            # Map model names to their classes
            model_map = {
                'store': StoreSettings,
                'notifications': NotificationSettings,
                'payments': PaymentSettings,
                'delivery': DeliverySettings,
                'tax': TaxSettings,
                'system': SystemSettings,
                'security': SecuritySettings,
            }
            
            for key, model_class in model_map.items():
                if key in data:
                    obj, created = model_class.objects.get_or_create(id=1)
                    fields = data[key].get('fields', {})
                    for field_name, value in fields.items():
                        if field_name != 'id' and hasattr(obj, field_name):
                            # Handle boolean fields
                            if value.lower() in ['true', 'false']:
                                value = value.lower() == 'true'
                            elif value == 'None':
                                value = None
                            # Handle Decimal fields
                            elif field_name in ['tax_rate', 'default_discount', 'delivery_fee', 'free_delivery_threshold']:
                                try:
                                    value = Decimal(value)
                                except:
                                    pass
                            setattr(obj, field_name, value)
                    obj.save()
            
            messages.success(request, 'Settings imported successfully! 📤')
        except Exception as e:
            messages.error(request, f'Error importing settings: {str(e)}')
        
        return redirect('core:settings')
    
    return redirect('core:settings')