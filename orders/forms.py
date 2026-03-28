from django import forms

from .models import Order


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ("full_name", "address", "phone", "payment_method")
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "payment_method": forms.Select(attrs={"class": "form-select"}),
        }


class RiderDeliveryConfirmationForm(forms.Form):
    signed_token = forms.CharField(widget=forms.HiddenInput())
