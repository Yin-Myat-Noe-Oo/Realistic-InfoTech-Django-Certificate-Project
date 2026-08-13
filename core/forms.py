from django import forms
from django.core.exceptions import ValidationError
from .models import Product, Category, Customer, Sale, Supplier

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'supplier', 'sku', 'barcode', 'description', 
                 'purchase_price', 'selling_price', 'quantity', 'reorder_level', 
                 'image', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'purchase_price': forms.NumberInput(attrs={'step': '0.01'}),
            'selling_price': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        purchase_price = cleaned_data.get('purchase_price')
        selling_price = cleaned_data.get('selling_price')

        if purchase_price and selling_price:
            if selling_price < purchase_price:
                raise ValidationError('Selling price must be greater than purchase price.')
        
        return cleaned_data

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'email', 'phone', 'address']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2}),
        }

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone', 'address']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2}),
        }

# core/forms.py

from django import forms
from .models import Sale

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['customer', 'payment_method', 'delivery_address', 'delivery_notes', 'notes']
        widgets = {
            'delivery_address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter delivery address...'}),
            'delivery_notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Special delivery instructions...'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Additional notes...'}),
        }

class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['status', 'tracking_number', 'courier_name', 'delivery_date', 'delivery_notes']
        widgets = {
            'delivery_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'delivery_notes': forms.Textarea(attrs={'rows': 2}),
        }