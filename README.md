Chococroco Order Management (Django + SQLite)
--------------------------------------------

Features included:
- Customer, Category, Size, Product, Order, Payment models
- Order calculations: product total, order total (with delivery), profit, cost total
- Admin actions to export selected Orders/Payments/Products to CSV
- Admin action to export Profit & Loss (CSV) for selected Orders
- Uses SQLite (db.sqlite3)

Quickstart:
1. unzip this project and 'cd' into it
2. create and activate a virtualenv
   python -m venv venv
   Windows: venv\Scripts\activate
   Linux/Mac: source venv/bin/activate
3. pip install -r requirements.txt
4. python manage.py makemigrations
5. python manage.py migrate
6. python manage.py createsuperuser
7. python manage.py runserver
8. Go to http://127.0.0.1:8000/admin/ and login
