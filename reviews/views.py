from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from products.models import Product

from .forms import ReviewForm
from .models import Review


@login_required
@require_POST
def submit_review(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    existing_review = Review.objects.filter(user=request.user, product=product).first()
    created = existing_review is None
    form = ReviewForm(request.POST, instance=existing_review)

    if form.is_valid():
        review = form.save(commit=False)
        review.user = request.user
        review.product = product
        review.save()
        messages.success(
            request,
            f"Your review for {product.name} has been {'saved' if created else 'updated'}.",
        )
    else:
        messages.error(request, "Please correct the review form and try again.")

    return redirect("products:product_detail", slug=product.slug)
