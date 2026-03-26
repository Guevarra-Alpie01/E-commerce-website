from django import forms


class CartAddProductForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 1}),
    )
    override = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.HiddenInput(),
    )
