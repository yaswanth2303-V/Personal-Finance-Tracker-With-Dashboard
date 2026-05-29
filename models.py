
from datetime import date
from django.db import models
from django.contrib.auth.models import User


# ---------------- Category ----------------
class Category(models.Model):
    
    name = models.CharField(max_length=100,unique=True)

    def __str__(self):
        return self.name

class Transaction(models.Model):
    TYPE_CHOICES = (
        ('Income', 'Income'),
        ('Expense', 'Expense')
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)  # ✅ this one
    amount = models.FloatField()
    date = models.DateField()
    description = models.TextField(blank=True)

    
    def __str__(self):
        return f"{self.user.username} - {self.type} - {self.amount}"


class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey("Category", on_delete=models.CASCADE, null=True, blank=True)  # ✅ added
    amount = models.FloatField(default=date.today)
    month = models.DateField()  
    limit = models.FloatField(default=0)   # ✅ added

    def remaining(self):
        """Returns the remaining budget for the month"""
        return max(0, self.limit - self.amount)

    def progress_percentage(self):
        """Returns how much of the budget is used in %"""
        if self.limit == 0:
            return 0
        return min(100, (self.amount/ self.limit) * 100)
    
    def __str__(self):
        month_str = self.month.strftime('%Y-%m')
        category_name = self.category.name if self.category else "General"
        return f"{self.user.username} - {category_name} ({month_str})"
    