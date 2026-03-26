# Lola Josie Tindahan

Lola Josie Tindahan is a full-stack Django e-commerce project that now uses:

- Django + SQLite for the backend
- Django REST Framework for storefront APIs
- React for the product catalog UI
- Bootstrap for the visual system
- Django admin plus a custom-branded admin dashboard for store management

## Main features

- User registration, login, logout, and profile management
- React-powered product catalog with search, category filter, pagination, and add-to-cart
- DRF endpoints for categories, products, and cart actions
- Session-based cart
- Cash on Delivery checkout
- Order history and status tracking
- Product reviews and ratings
- Stock validation and inventory reduction during checkout
- Custom-branded admin and staff dashboard

## Project structure

- `users/`: auth-related pages, profile page, staff dashboard, admin template tags
- `products/`: catalog models, detail page, storefront entry template
- `cart/`: session cart helper and cart views
- `orders/`: checkout flow and order tracking
- `reviews/`: review form and submission logic
- `api/`: DRF serializers, API views, and API URL routes
- `frontend/`: React + Bootstrap source code built into `static/frontend/`

## Backend setup

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## Frontend setup

The built React assets are already checked into `static/frontend/`, so the Django app can run without Node in production.

If you want to edit the React UI:

```bash
cd frontend
npm install
npm run build
```

That rebuilds:

- `static/frontend/storefront.js`
- `static/frontend/storefront.css`

## Environment variables

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`

## Static and media files

- Product images upload to `media/products/`
- React and Bootstrap build output is stored in `static/frontend/`
- Deployment static output is collected into `staticfiles/`

Before deployment:

```bash
python manage.py collectstatic --noinput
```

## PythonAnywhere notes

- This project still avoids Celery, Redis, WebSockets, and external APIs.
- Because the React bundle is prebuilt into Django static files, you do not need Node on PythonAnywhere just to serve the app.
- If you change the React source locally, rebuild it before uploading or redeploying.

## Useful commands

```bash
python manage.py test
python manage.py check
python manage.py collectstatic --noinput
```
