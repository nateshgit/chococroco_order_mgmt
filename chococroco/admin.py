from django.contrib import admin
from django.http import HttpResponse, HttpResponseRedirect
import csv
from .models import Customer, Category, Size, Product, Order, Payment
from django.utils.html import format_html
from django import forms
from django.shortcuts import get_object_or_404
from django.urls import path, reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


def export_as_csv_action(description="Export selected rows as CSV"):
    def export_as_csv(modeladmin, request, queryset):
        meta = modeladmin.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename={meta}.csv'
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            row = [getattr(obj, field) for field in field_names]
            writer.writerow(row)
        return response
    export_as_csv.short_description = description
    return export_as_csv

def export_profit_loss_csv(modeladmin, request, queryset):
    orders = queryset
    total_revenue = sum([o.order_total() for o in orders])
    total_cost = sum([o.cost_total() for o in orders])
    total_profit = total_revenue - total_cost

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=profit_loss.csv'
    writer = csv.writer(response)
    writer.writerow(['Total Revenue', 'Total Cost', 'Total Profit'])
    writer.writerow([str(total_revenue), str(total_cost), str(total_profit)])
    writer.writerow([])
    writer.writerow(['Order ID','Customer','Product','Quantity','Product Total','Delivery Cost','Order Total','Profit'])
    for o in orders:
        writer.writerow([o.id, o.customer.name, o.product.name, o.quantity, str(o.product_total()), str(o.delivery_cost), str(o.order_total()), str(o.profit())])
    return response
export_profit_loss_csv.short_description = "Export Profit/Loss for selected orders (CSV)"

class PaymentInline(admin.TabularInline):  # or admin.StackedInline for a different layout
    model = Payment
    extra = 1  # Number of empty payment forms to display

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name','email','phone')
    actions = [export_as_csv_action("Export Customers as CSV")]

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'category', 'size', 'cost_price', 'sell_price', 'product_image_preview')  # Use display_name here
    search_fields = ('name',)
    actions = [export_as_csv_action("Export Products as CSV")]
    readonly_fields = ('display_name', 'product_image_preview') # Added this line

    def product_image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "No Image"
    product_image_preview.short_description = 'Image Preview'
    product_image_preview.allow_tags = True

class OrderChangeForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].label_from_instance = lambda obj: obj.display_name

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'product_display_name', 'quantity', 'order_total_display', 'order_image_preview',
                    'payment_status', 'order_status', 'created_at', 'other_expense', 'profit_amount') # ADDED other expense
    list_filter = ('order_status', 'payment_status', 'created_at', 'product__category')
    search_fields = ('customer__name', 'product__name')
    actions = [export_as_csv_action("Export Orders as CSV"), export_profit_loss_csv, "download_invoice"]
    inlines = [PaymentInline]
    form = OrderChangeForm
    change_form_template = 'admin/order_change_form.html'

    def product_display_name(self, obj):
        return obj.product.display_name  # Retrieve from the display_name field
    product_display_name.short_description = 'Product'

    def order_image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "No Image"
    order_image_preview.short_description = 'Image Preview'  # Added here
    order_image_preview.allow_tags = True #Added here

    def product_total_display(self, obj):
        return obj.product_total()
    product_total_display.short_description = 'Product Total'

    def order_total_display(self, obj):
        return obj.order_total()
    order_total_display.short_description = 'Order Total'

    def profit_display(self, obj):
        return obj.profit()
    profit_display.short_description = 'Profit'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:order_id>/invoice/', self.admin_site.admin_view(self.download_invoice_view), name="order-invoice"),
            path('<int:order_id>/delivery_slip/', self.admin_site.admin_view(self.delivery_slip_view), name="chococroco_order-delivery-slip"),
        ]
        return custom_urls + urls

    def download_invoice_view(self, request, order_id, *args, **kwargs):
        order = get_object_or_404(Order, pk=order_id)
        return order.generate_invoice()

    def delivery_slip_view(self, request, order_id, *args, **kwargs):
        order = get_object_or_404(Order, pk=order_id)
        return self.generate_delivery_slip(order)

    def generate_delivery_slip(self, order):
        # Implement your delivery slip generation logic here
        # This is just a placeholder
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="delivery_slip_{order.id}.txt"'
        # Company Details (Replace with your actual details)
        company_name = "ChocoCroco Orders"
        company_address = "123 Main Street, Anytown"
        company_phone = "555-123-4567"

        # Customer Details
        customer_name = order.customer.name
        customer_address = order.customer.address
        customer_phone = order.customer.phone

        # Format the delivery slip content
        delivery_slip_content = f"""
        --- {company_name} ---
        {company_address}
        {company_phone}

        --- Delivery To ---
        {customer_name}
        {customer_address}
        {customer_phone}

        Order ID: {order.id}
        """
        response.write(delivery_slip_content)
        return response

    def download_invoice(self, request, queryset):
        if queryset.count() == 1:
            order = queryset.first()
            return HttpResponseRedirect(reverse('admin:order-invoice', args=[order.pk]))
        self.message_user(request, "Please select exactly one order.")
    download_invoice.short_description = "Download Invoice PDF"

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        order = get_object_or_404(Order, pk=object_id)
        invoice_url = reverse('admin:order-invoice', args=[order.pk])
        delivery_slip_url = reverse('admin:chococroco_order-delivery-slip', args=[order.pk])
        extra_context['invoice_url'] = invoice_url
        extra_context['delivery_slip_url'] = delivery_slip_url
        form = OrderChangeForm(instance=order)
        extra_context['form'] = form
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def save_model(self, request, obj, form, change):
        obj.save()

    def render_change_form(self, request, context, add=False, change=False, form_url=None, obj=None):
        #context['show_save'] = False
        context['show_save_and_continue'] = False
        context['show_save_and_add_another'] = False
        return super().render_change_form(request, context, add, change, form_url, obj)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id','order','amount','method','payment_date')
    actions = [export_as_csv_action("Export Payments as CSV")]
