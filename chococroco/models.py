from django.db import models
from django.utils import timezone
from django.http import FileResponse
import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors


class Customer(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Size(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Product(models.Model):
    display_name = models.CharField(max_length=200, blank=True, null=True)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sell_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)  # Added image field

    def __str__(self):
        return self.display_name if self.display_name else self.name

    def save(self, *args, **kwargs):
        if self.size:
            self.display_name = f"{self.name} - {self.size.name}"
        else:
            self.display_name = self.name
        super().save(*args, **kwargs)


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    PAYMENT_CHOICES = [
        ('pending', 'Pending'),
        ('partial_paid', 'Partial Paid'),
        ('full_paid', 'Full Paid'),
        ('refunded', 'Refunded'),
    ]
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_expense = models.DecimalField(max_digits=10, decimal_places=2, default=0) # ADDED other expense
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    received_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pending_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    order_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='order_images/', blank=True, null=True)
    profit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0) # Added profit amount

    def product_total(self):
        return self.product.sell_price * self.quantity

    def order_total(self):
        return self.product_total() + self.delivery_cost

    def profit(self):
        return (self.product.sell_price - self.product.cost_price) * self.quantity - self.other_expense

    def cost_total(self):
        return self.product.cost_price * self.quantity + self.delivery_cost + self.other_expense

    def save(self, *args, **kwargs):
        self.total = self.order_total()
        self.pending_amount = self.total - self.received_amount
        self.profit_amount = self.profit() # Calculate and store profit
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.id} - {self.customer.name}"

    # ✅ Invoice PDF generator
    def generate_invoice(self):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        # --- Header ---
        company_info = Paragraph(
            "<b>ChocoCroco Pvt Ltd</b><br/>123, Sweet Street<br/>Chennai, India<br/>Phone: +91-9876543210",
            styles['Normal']
        )
        header_table = Table([["Company Logo", company_info]], colWidths=[120, 380])
        elements.append(header_table)
        elements.append(Spacer(1, 20))

        # --- Customer + Order Info ---
        customer_details = Paragraph(
            f"<b>Customer:</b> {self.customer.name}<br/>{self.customer.address}",
            styles['Normal']
        )
        order_details = Paragraph(
            f"<b>Order No:</b> {self.id}<br/><b>Date:</b> {self.created_at.strftime('%d-%m-%Y')}",
            styles['Normal']
        )
        cust_order_table = Table([[customer_details, order_details]], colWidths=[250, 250])
        elements.append(cust_order_table)
        elements.append(Spacer(1, 20))

        # --- Order Items Table ---
        data = [["Product", "Quantity", "Rate", "Total"]]
        data.append([
            self.product.display_name if self.product.display_name else self.product.name,
            self.quantity,
            f"₹{self.product.sell_price}",
            f"₹{self.product_total()}",
        ])

        data.append(["", "", "Subtotal", f"₹{self.product_total()}"])
        data.append(["", "", "Delivery Cost", f"₹{self.delivery_cost}"])
        data.append(["", "", "Other Expense", f"₹{self.other_expense}"]) # ADDED other expense
        data.append(["", "", "Grand Total", f"₹{self.total}"])
        data.append(["", "", "Profit", f"₹{self.profit_amount}"]) # Added profit amount

        table = Table(data, colWidths=[200, 80, 100, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f2f2f2")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 20))

        # --- Footer ---
        footer = Paragraph(
            "<b>Thanks for your order!</b><br/>Follow us on Instagram, Facebook, YouTube",
            styles['Normal']
        )
        elements.append(footer)

        doc.build(elements)
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename=f"invoice_{self.id}.pdf")


class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(
        max_length=50,
        choices=[('cash', 'Cash'), ('upi', 'UPI'), ('card', 'Card')],
        default='cash'
    )
    payment_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Payment {self.id} - {self.amount}"
