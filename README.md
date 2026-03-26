# Django E-Commerce Store

A full-stack Django e-commerce web application designed for a simple deployment target such as the PythonAnywhere free plan.

## Features

- User registration, login, logout, and profile management
- Product catalog with categories, search, filtering, and pagination
- Session-based shopping cart with quantity updates and cart count in the navbar
- Checkout with Cash on Delivery only
- Orders and order items stored in SQLite
- Order history and order status tracking
- Product reviews and ratings from authenticated users only
- Inventory reduction at checkout and stock validation
- Django admin customizations for products, users, orders, and reviews
- Responsive Django template frontend with local static assets only

## App structure

- `users`: registration, profile page, simple staff dashboard
- `products`: categories, products, catalog pages
- `cart`: session cart helpers and cart pages
- `orders`: checkout, order history, order detail
- `reviews`: product review submission and management

## Local setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Apply migrations:

```bash
python manage.py migrate
```

4. Create an admin user:

```bash
python manage.py createsuperuser
```

5. Run the development server:

```bash
python manage.py runserver
```

6. Open `http://127.0.0.1:8000/`.

## Environment variables

The project reads configuration from environment variables:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`

For local development, the defaults are enough to start quickly. For production, set all of them explicitly.

## Static and media files

- Product uploads are stored in `media/products/`
- Static assets live in `static/`
- Deployment static output is collected into `staticfiles/`

Run this before deployment:

```bash
python manage.py collectstatic --noinput
```

## PythonAnywhere free plan deployment

This project avoids Celery, Redis, WebSockets, background workers, and external APIs, so it fits the PythonAnywhere free plan well.

1. Upload the project to PythonAnywhere.
2. Open a Bash console and create a virtual environment that uses Python 3.12+.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set environment variables in your console startup file or directly in the WSGI file:

```bash
export DJANGO_SECRET_KEY='replace-me'
export DJANGO_DEBUG=False
export DJANGO_ALLOWED_HOSTS='yourusername.pythonanywhere.com'
export DJANGO_CSRF_TRUSTED_ORIGINS='https://yourusername.pythonanywhere.com'
```

5. Run database migrations:

```bash
python manage.py migrate
```

6. Collect static files:

```bash
python manage.py collectstatic --noinput
```

7. In the PythonAnywhere Web tab:
   - Create a new web app using Manual configuration.
   - Point it to the same Python version as your virtual environment.
   - Set the source code path to your project folder.
   - Add a static files mapping for `/static/` to `/home/yourusername/your-project/staticfiles`
   - Add a static files mapping for `/media/` to `/home/yourusername/your-project/media`

8. Edit the generated WSGI file so it adds your project path and activates your virtual environment if needed. The default Django WSGI entry should point to `config.settings`.

9. Reload the web app from the Web tab.

## Useful management commands

```bash
python manage.py test
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

## Notes

- SQLite is used by default for simplicity and PythonAnywhere compatibility.
- Only authenticated users can place orders and submit reviews.
- The cart is session-based, so no cart table is required in the database.
