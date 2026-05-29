from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Category, Transaction, Budget

# --- Category Admin ---
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    ordering = ('id',)


# --- Transaction Admin ---
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'type', 'category', 'amount', 'date')
    list_filter = ('type', 'category', 'date')
    search_fields = ('user__username', 'category__name')
    ordering = ('-date',)
    date_hierarchy = 'date'
    actions = ['delete_selected']  # ✅ Enable bulk delete


# --- Budget Admin ---
@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'category', 'month', 'limit', 'amount')
    list_filter = ('month', 'category')
    search_fields = ('user__username', 'category__name')
    ordering = ('-month',)
    actions = ['delete_selected']  # ✅ Enable bulk delete


# --- Transaction Inline (inside User page) ---
class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    readonly_fields = ('date', 'amount', 'type', 'category')
    can_delete = False


# --- Custom User Admin with inline transactions ---
admin.site.unregister(User)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [TransactionInline]


# --- Optional: Admin Site Branding ---
admin.site.site_header = "💰 Personal Finance Tracker Admin"
admin.site.site_title = "Finance Tracker Admin"
admin.site.index_title = "Manage Users, Transactions, and Budgets"
