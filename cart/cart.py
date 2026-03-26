from decimal import Decimal

from products.models import Product


class Cart:
    SESSION_KEY = "cart"

    def __init__(self, request):
        self.session = request.session
        self.cart = self.session.get(self.SESSION_KEY, {})

    def add(self, product, quantity=1, override_quantity=False):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = 0

        if override_quantity:
            self.cart[product_id] = quantity
        else:
            self.cart[product_id] += quantity

        if self.cart[product_id] <= 0:
            del self.cart[product_id]

        self.save()

    def save(self):
        self.session[self.SESSION_KEY] = self.cart
        self.session.modified = True

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def clear(self):
        self.session.pop(self.SESSION_KEY, None)
        self.session.modified = True
        self.cart = {}

    def get_quantity(self, product):
        return self.cart.get(str(product.id), 0)

    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids, is_active=True).select_related("category")
        available_ids = {str(product.id) for product in products}

        missing_ids = [product_id for product_id in self.cart.keys() if product_id not in available_ids]
        if missing_ids:
            for product_id in missing_ids:
                del self.cart[product_id]
            self.save()

        for product in products:
            quantity = self.cart[str(product.id)]
            yield {
                "product": product,
                "quantity": quantity,
                "price": product.price,
                "total_price": product.price * quantity,
            }

    def __len__(self):
        return sum(self.cart.values())

    def get_subtotal_price(self):
        return sum(
            (item["price"] * item["quantity"] for item in self),
            start=Decimal("0.00"),
        )
