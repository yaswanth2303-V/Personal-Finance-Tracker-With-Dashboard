# tracker/forms.py
from django import forms 
from .models import Transaction
from .models import Budget

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['description', 'amount', 'category', 'type', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.TextInput(attrs={'class': 'form-control','placeholder': 'Enter description'}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
        }



class BudgetForm(forms.ModelForm):
    
    month = forms.DateField(
        widget=forms.DateInput(attrs={"type": "month"})
    )

    class Meta:
        model = Budget
        fields = ['category', 'month', 'amount']