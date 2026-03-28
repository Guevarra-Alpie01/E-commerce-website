from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from orders.models import Order, Payment
from products.models import Category, Product
from users.models import UserProfile


class AdminStyledFormMixin:
    def apply_bootstrap(self):
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                css_class = "form-check-input"
            elif isinstance(widget, forms.Select):
                css_class = "form-select"
            else:
                css_class = "form-control"
            existing_classes = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing_classes} {css_class}".strip()


class AdminAuthenticationForm(AdminStyledFormMixin, AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"placeholder": "Admin username"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "Password"}))

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request=request, *args, **kwargs)
        self.apply_bootstrap()


class AdminUserForm(AdminStyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "username", "email", "is_active", "is_staff", "is_superuser")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


class AdminUserProfileForm(AdminStyledFormMixin, forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = (
            "role",
            "phone",
            "address",
            "city",
            "postal_code",
            "delivery_zone",
            "vehicle_details",
        )
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


class AdminRiderCreationForm(AdminStyledFormMixin, UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    phone = forms.CharField(max_length=20, required=False)
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))
    city = forms.CharField(max_length=120, required=False)
    postal_code = forms.CharField(max_length=20, required=False)
    delivery_zone = forms.CharField(max_length=120, required=False)
    vehicle_details = forms.CharField(max_length=120, required=False)
    is_active = forms.BooleanField(required=False, initial=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.is_active = self.cleaned_data["is_active"]
        if commit:
            user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = UserProfile.Role.RIDER
            profile.phone = self.cleaned_data["phone"]
            profile.address = self.cleaned_data["address"]
            profile.city = self.cleaned_data["city"]
            profile.postal_code = self.cleaned_data["postal_code"]
            profile.delivery_zone = self.cleaned_data["delivery_zone"]
            profile.vehicle_details = self.cleaned_data["vehicle_details"]
            profile.save()
        return user


class AdminProductForm(AdminStyledFormMixin, forms.ModelForm):
    class Meta:
        model = Product
        fields = ("category", "name", "description", "price", "stock", "image", "is_active")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


class AdminCategoryForm(AdminStyledFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name", "description")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


class AdminOrderStatusForm(AdminStyledFormMixin, forms.ModelForm):
    class Meta:
        model = Order
        fields = ("assigned_rider", "status")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_rider"].required = False
        self.fields["assigned_rider"].queryset = (
            User.objects.select_related("profile")
            .filter(profile__role=UserProfile.Role.RIDER)
            .order_by("first_name", "username")
        )
        self.apply_bootstrap()

    def clean(self):
        cleaned_data = super().clean()
        assigned_rider = cleaned_data.get("assigned_rider")
        status = cleaned_data.get("status")
        rider_required_statuses = {
            Order.Status.ASSIGNED,
            Order.Status.OUT_FOR_DELIVERY,
        }
        if status in rider_required_statuses and assigned_rider is None:
            self.add_error("assigned_rider", "Assign a rider before moving this order into a rider-managed status.")
        return cleaned_data


class AdminPaymentStatusForm(AdminStyledFormMixin, forms.ModelForm):
    class Meta:
        model = Payment
        fields = ("status", "notes")
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()
