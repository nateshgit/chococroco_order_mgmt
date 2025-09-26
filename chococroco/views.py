from django.shortcuts import render
from django.db.models import Sum, F
from .models import Order

def order_report(request):
    # Filters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status = request.GET.get('status')

    orders = Order.objects.all()

    if start_date:
        orders = orders.filter(created_at__date__gte=start_date)
    if end_date:
        orders = orders.filter(created_at__date__lte=end_date)
    if status:
        orders = orders.filter(order_status=status)

    # Aggregations
    total_sales = orders.aggregate(total=Sum('total'))['total'] or 0
    total_profit = orders.aggregate(total=Sum('profit_amount'))['total'] or 0
    total_cost = sum(o.cost_total() for o in orders)

    return render(request, "reports/order_report.html", {
        "orders": orders,
        "total_sales": total_sales,
        "total_profit": total_profit,
        "total_cost": total_cost,
        "filters": {"start_date": start_date, "end_date": end_date, "status": status}
    })
