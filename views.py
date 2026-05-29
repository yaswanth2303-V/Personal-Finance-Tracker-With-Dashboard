from decimal import Decimal
from datetime import datetime

from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Q
from django.db.models.functions import TruncMonth
from django.db.models import Sum
from .models import Transaction, Budget, Category # your models
from .forms import TransactionForm,BudgetForm
from django.http import HttpResponse
import json
import csv



def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "❌ Passwords do not match")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "⚠️ Username already taken")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "⚠️ Email already registered")
            return redirect("register")

        # Create user
        user = User.objects.create_user(username=username, email=email, password=password1)
        user.save()
        messages.success(request, "✅ Account created successfully. Please log in.")
        return redirect("login")

    return render(request, "tracker/register.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect("dashboard")
        messages.error(request, "Invalid credentials!")
        return redirect("login")

    return render(request, "tracker/login.html")

@login_required
def home(request):
    """Redirect /home/ or / to dashboard."""
    return redirect("dashboard")

@login_required
def logout_view(request):
    logout(request)
    return redirect("login")

def export_csv(request):
    # Only export user's transactions
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Category', 'Type', 'Amount'])  # Clean headers

    for t in transactions:
        writer.writerow([
            t.date.strftime('%d-%b-%Y'),
            t.category.name if t.category else "N/A",
            t.type,
            round(float(t.amount), 2)   # ✅ clean numeric value
        ])

    return response

@login_required
def dashboard(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')

  # --- Filters ---
    month = request.GET.get('month')
    category_id = request.GET.get('category')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if month:
        year, m = map(int, month.split('-'))
        transactions = transactions.filter(date__year=year, date__month=m)
    if category_id:
        transactions = transactions.filter(category_id=category_id)
    if start_date and end_date:
        transactions = transactions.filter(date__range=[start_date, end_date])

    # --- Summary ---
    income = transactions.filter(type='Income').aggregate(total=Sum('amount'))['total'] or 0
    expense = transactions.filter(type='Expense').aggregate(total=Sum('amount'))['total'] or 0
    balance = income - expense

    # --- Pie Chart (Category-wise Expense) ---
    categories = Category.objects.all()
    pie_labels, pie_data = [], []
    for c in categories:
        total = transactions.filter(type='Expense', category=c).aggregate(total=Sum('amount'))['total'] or 0
        if total > 0:
            pie_labels.append(c.name)
            pie_data.append(float(total)) # ✅ Convert Decimal → float

    # --- Bar/Line Chart (Monthly Trend) ---
    monthly = (
        transactions.annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(
            income=Sum('amount', filter=Q(type='Income')),
            expense=Sum('amount', filter=Q(type='Expense'))
        )
        .order_by('month')
    )

    months = [m['month'].strftime('%Y-%m') for m in monthly]
    income_data = [float(m['income'] or 0) for m in monthly]
    expense_data = [float(m['expense'] or 0) for m in monthly]

    context = {
        'transactions': transactions,
        'income': income,
        'expense': expense,
        'balance': balance,
        'categories': categories,
        "selected_currency": request.session.get("currency", "INR"),
        'selected_month': month,
        'selected_category': category_id,
        'start_date': start_date,
        'end_date': end_date,
        # charts
        "pie_labels": json.dumps(pie_labels),
        "pie_data": json.dumps(pie_data),
        "months": json.dumps(months),
        "income_data": json.dumps(income_data),
        "expense_data": json.dumps(expense_data),
    }   

    return render(request, 'tracker/dashboard.html', context)

# ---------------- Transactions ----------------
@login_required
def transactions_list(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')

    # Optional filters
    type_filter = request.GET.get('type')
    category_filter = request.GET.get('category')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if type_filter and type_filter != "All":
        transactions = transactions.filter(type=type_filter)
    if category_filter and category_filter != "All":
        transactions = transactions.filter(category__id=category_filter)
    if start_date:
        transactions = transactions.filter(date__gte=start_date)
    if end_date:
        transactions = transactions.filter(date__lte=end_date)

    categories = Category.objects.all()
    context = {
        'transactions': transactions,
        'categories': categories,
    }
    return render(request, 'tracker/transactions_list.html',{"transactions": transactions}) 

 

@login_required
def add_transaction(request):
    categories = Category.objects.all()

    if request.method == "POST":
        description = request.POST.get("description")
        amount = request.POST.get("amount")
        category_id = request.POST.get("category")
        transaction_type = request.POST.get("transaction_type")
        date_value = request.POST.get("date")

        category = get_object_or_404(Category, id=category_id)
        Transaction.objects.create(
            user=request.user,
            description=description,
            category=category,
            amount=amount,
            type=transaction_type,
            date=date_value
        )
        return redirect("dashboard")
    form = TransactionForm(request.POST)
    if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            messages.success(request, "Transaction added successfully!")
            return redirect("transactions_list")
    else:

       form = TransactionForm()

    return render(request, "tracker/add_transaction.html", {"categories": categories, "form": form})


@login_required
def edit_transaction(request, id):
    transaction = get_object_or_404(Transaction, id=id, user=request.user)
    categories = Category.objects.all()

    if request.method == "POST":
        transaction.description = request.POST['description']
        transaction.amount = Decimal(request.POST['amount'])
        transaction.type = request.POST['transaction_type']
        transaction.date = request.POST['date']
        transaction.category = get_object_or_404(Category, id=request.POST['category'])
        transaction.save()
        return redirect("dashboard")
    form = TransactionForm(request.POST, instance=transaction)
    if form.is_valid():
            form.save()
            messages.success(request, "Transaction updated successfully!")
            return redirect("transactions_list")
    else:
        form = TransactionForm(instance=transaction)

    return render(request, "tracker/edit_transaction.html", {"transaction": transaction, "categories": categories})


@login_required
def delete_transaction(request, id):
    transaction = get_object_or_404(Transaction, id=id, user=request.user)
    transaction.delete()
    messages.success(request, "Transaction deleted successfully.")
    return redirect("dashboard")

@login_required
def charts_view(request):
    # Fetch all user transactions
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')

    # Pie chart: Expense by Category
    categories = Category.objects.all()
    pie_labels, pie_data = [], []
    for c in categories:
        total = transactions.filter(type='Expense', category=c).aggregate(total=Sum('amount'))['total'] or 0
        if total > 0:
            pie_labels.append(c.name)
            pie_data.append(total)

    # Line chart: Monthly Income/Expense
    monthly = transactions.annotate(month=TruncMonth('date')).values('month').annotate(
        income=Sum('amount', filter=Q(type='Income')),
        expense=Sum('amount', filter=Q(type='Expense'))
    ).order_by('month')

    months = [m['month'].strftime('%Y-%m') for m in monthly]
    income_data = [m['income'] or 0 for m in monthly]
    expense_data = [m['expense'] or 0 for m in monthly]

    context = {
        'pie_labels': pie_labels,
        'pie_data': pie_data,
        'months': months,
        'income_data': income_data,
        'expense_data': expense_data,
    }

    return render(request, 'tracker/charts.html', context)

@login_required
def budget_view(request):
    # --- Determine selected month ---
    month_str = request.GET.get('month')
    today = datetime.today()
    if month_str:
        year, month = map(int, month_str.split('-'))
    else:
        year, month = today.year, today.month
    month_date = datetime(year, month, 1)

    # --- Safely get or create one budget ---
    budget_qs = Budget.objects.filter(user=request.user, month=month_date)
    if budget_qs.exists():
        budget = budget_qs.first()  # ✅ Get first if duplicates
    else:
        budget = Budget.objects.create(user=request.user, month=month_date, amount=0, limit=0)  # ✅ Explicit values

    # --- Handle POST ---
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget)
        if form.is_valid():
            form.instance.user = request.user
            month_input = form.cleaned_data['month']
            form.instance.month = datetime(month_input.year, month_input.month, 1)
            form.save()
            messages.success(request, "✅ Budget updated successfully!")
            return redirect('budget')
    else:
        form = BudgetForm(instance=budget)

    # --- Calculate total spent ---
    spent = Transaction.objects.filter(
        user=request.user,
        type='Expense',
        date__year=month_date.year,
        date__month=month_date.month
    ).aggregate(total=Sum('amount'))['total'] or 0

    budget_amount = budget.amount or 0
    percent = (spent / budget_amount * 100) if budget_amount > 0 else 0

    context = {
        'form': form,
        'spent': spent,
        'budget_amount': budget_amount,
        'percent': percent,
        'month': month_date.strftime("%Y-%m"),
    }
    return render(request, 'tracker/budget.html', context)
