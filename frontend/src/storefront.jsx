import React, { startTransition, useDeferredValue, useEffect, useMemo, useState } from "react";

const currencyFormatter = new Intl.NumberFormat("en-PH", {
  style: "currency",
  currency: "PHP",
});

function getCookie(name) {
  const cookies = document.cookie ? document.cookie.split(";") : [];
  for (const cookie of cookies) {
    const trimmed = cookie.trim();
    if (trimmed.startsWith(`${name}=`)) {
      return decodeURIComponent(trimmed.slice(name.length + 1));
    }
  }
  return "";
}

async function readJson(response) {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "Something went wrong.");
  }
  return payload;
}

function buildProductsUrl(baseUrl, { search, category, page }) {
  const url = new URL(baseUrl, window.location.origin);
  if (search) {
    url.searchParams.set("search", search);
  }
  if (category) {
    url.searchParams.set("category", category);
  }
  if (page > 1) {
    url.searchParams.set("page", String(page));
  }
  return url.toString();
}

function syncBrowserUrl(search, category, page) {
  const url = new URL(window.location.href);
  if (search) {
    url.searchParams.set("q", search);
  } else {
    url.searchParams.delete("q");
  }
  if (category) {
    url.searchParams.set("category", category);
  } else {
    url.searchParams.delete("category");
  }
  if (page > 1) {
    url.searchParams.set("page", String(page));
  } else {
    url.searchParams.delete("page");
  }
  window.history.replaceState({}, "", url);
}

function HeroCard({ selectedCategoryName, productCount, cartSubtotal }) {
  return (
    <section className="lj-hero card border-0 shadow-sm mb-4">
      <div className="card-body p-4 p-lg-5">
        <div className="row align-items-center g-4">
          <div className="col-lg-8">
            <span className="badge text-bg-warning text-uppercase mb-3 px-3 py-2 rounded-pill">
              Lola Josie Tindahan
            </span>
            <h1 className="display-6 fw-bold mb-3">A neighborhood store, now online.</h1>
            <p className="lead text-secondary mb-0">
              Browse pantry picks, home finds, and everyday favorites with a warm, Bootstrap-powered storefront
              backed by Django REST and React.
            </p>
          </div>
          <div className="col-lg-4">
            <div className="p-4 rounded-4 bg-white bg-opacity-75 border">
              <div className="d-flex justify-content-between mb-2">
                <span className="text-secondary">Visible products</span>
                <strong>{productCount}</strong>
              </div>
              <div className="d-flex justify-content-between mb-2">
                <span className="text-secondary">Category</span>
                <strong>{selectedCategoryName || "All items"}</strong>
              </div>
              <div className="d-flex justify-content-between">
                <span className="text-secondary">Cart subtotal</span>
                <strong>{currencyFormatter.format(Number(cartSubtotal || 0))}</strong>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function Filters({ categories, selectedCategory, setSelectedCategory, searchInput, setSearchInput }) {
  return (
    <div className="card border-0 shadow-sm mb-4">
      <div className="card-body p-4">
        <div className="row g-3 align-items-end">
          <div className="col-lg-7">
            <label className="form-label fw-semibold" htmlFor="storefront-search">
              Search products
            </label>
            <input
              id="storefront-search"
              className="form-control form-control-lg"
              placeholder="Try coffee, tote, snacks, planner..."
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
            />
          </div>
          <div className="col-lg-5">
            <label className="form-label fw-semibold" htmlFor="storefront-category">
              Filter by category
            </label>
            <select
              id="storefront-category"
              className="form-select form-select-lg"
              value={selectedCategory}
              onChange={(event) => setSelectedCategory(event.target.value)}
            >
              <option value="">All categories</option>
              {categories.map((category) => (
                <option key={category.id} value={category.slug}>
                  {category.name} ({category.product_count})
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>
    </div>
  );
}

function ProductCard({ product, onAddToCart }) {
  const averageRating = product.avg_rating ? Number(product.avg_rating).toFixed(1) : "0.0";

  return (
    <article className="col">
      <div className="card h-100 border-0 shadow-sm overflow-hidden product-card">
        <a href={product.detail_url} className="text-decoration-none">
          {product.image_url ? (
            <img src={product.image_url} className="card-img-top product-image" alt={product.name} />
          ) : (
            <div className="product-image product-image-placeholder d-flex align-items-center justify-content-center">
              No image yet
            </div>
          )}
        </a>
        <div className="card-body d-flex flex-column">
          <div className="d-flex justify-content-between align-items-start gap-3 mb-2">
            <span className="badge rounded-pill text-bg-light border text-secondary">{product.category_name}</span>
            <span className="small text-secondary">{averageRating} / 5</span>
          </div>
          <h2 className="h5">
            <a href={product.detail_url} className="stretched-link text-decoration-none text-dark">
              {product.name}
            </a>
          </h2>
          <p className="text-secondary flex-grow-1 mb-3">{product.description}</p>
          <div className="d-flex justify-content-between align-items-center mb-3">
            <strong className="text-danger fs-5">{currencyFormatter.format(Number(product.price))}</strong>
            <span className={`badge rounded-pill ${product.stock > 0 ? "text-bg-success" : "text-bg-secondary"}`}>
              {product.stock > 0 ? `${product.stock} in stock` : "Out of stock"}
            </span>
          </div>
          <button
            type="button"
            className="btn btn-dark mt-auto"
            disabled={product.stock < 1}
            onClick={() => onAddToCart(product.id)}
          >
            Add to cart
          </button>
        </div>
      </div>
    </article>
  );
}

function Pagination({ page, pages, onPageChange }) {
  if (pages <= 1) {
    return null;
  }

  const visiblePages = [];
  for (let pageNumber = 1; pageNumber <= pages; pageNumber += 1) {
    visiblePages.push(pageNumber);
  }

  return (
    <nav aria-label="Storefront pages" className="d-flex justify-content-center mt-4">
      <ul className="pagination pagination-lg flex-wrap">
        <li className={`page-item ${page === 1 ? "disabled" : ""}`}>
          <button className="page-link" type="button" onClick={() => onPageChange(page - 1)}>
            Previous
          </button>
        </li>
        {visiblePages.map((pageNumber) => (
          <li key={pageNumber} className={`page-item ${pageNumber === page ? "active" : ""}`}>
            <button className="page-link" type="button" onClick={() => onPageChange(pageNumber)}>
              {pageNumber}
            </button>
          </li>
        ))}
        <li className={`page-item ${page === pages ? "disabled" : ""}`}>
          <button className="page-link" type="button" onClick={() => onPageChange(page + 1)}>
            Next
          </button>
        </li>
      </ul>
    </nav>
  );
}

export function StorefrontApp({ config }) {
  const [searchInput, setSearchInput] = useState(config.initialSearch || "");
  const deferredSearch = useDeferredValue(searchInput);
  const [selectedCategory, setSelectedCategory] = useState(config.initialCategory || "");
  const [page, setPage] = useState(() => Number(new URLSearchParams(window.location.search).get("page")) || 1);
  const [categories, setCategories] = useState([]);
  const [catalog, setCatalog] = useState({ results: [], page: 1, pages: 1, count: 0 });
  const [cartSummary, setCartSummary] = useState({ item_count: 0, subtotal: "0.00" });
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const selectedCategoryName = useMemo(
    () => categories.find((category) => category.slug === selectedCategory)?.name || "",
    [categories, selectedCategory],
  );

  useEffect(() => {
    if (page !== 1) {
      setPage(1);
    }
  }, [deferredSearch, selectedCategory]);

  useEffect(() => {
    let cancelled = false;

    async function loadCategories() {
      const categoryResponse = await fetch(config.categoriesApi, {
        headers: { Accept: "application/json" },
      });
      const categoryPayload = await readJson(categoryResponse);
      if (!cancelled) {
        startTransition(() => {
          setCategories(categoryPayload);
        });
      }
    }

    async function loadCartSummary() {
      const cartResponse = await fetch(config.cartSummaryApi, {
        headers: { Accept: "application/json" },
      });
      const cartPayload = await readJson(cartResponse);
      if (!cancelled) {
        startTransition(() => {
          setCartSummary(cartPayload);
          const cartBadge = document.getElementById("cart-count-badge");
          if (cartBadge) {
            cartBadge.textContent = cartPayload.item_count;
          }
        });
      }
    }

    Promise.all([loadCategories(), loadCartSummary()]).catch((loadError) => {
      if (!cancelled) {
        setError(loadError.message);
      }
    });

    return () => {
      cancelled = true;
    };
  }, [config.cartSummaryApi, config.categoriesApi]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    syncBrowserUrl(deferredSearch, selectedCategory, page);

    async function loadProducts() {
      const productResponse = await fetch(
        buildProductsUrl(config.productsApi, {
          search: deferredSearch,
          category: selectedCategory,
          page,
        }),
        { headers: { Accept: "application/json" } },
      );
      const payload = await readJson(productResponse);
      if (!cancelled) {
        startTransition(() => {
          setCatalog(payload);
          setLoading(false);
        });
      }
    }

    loadProducts().catch((loadError) => {
      if (!cancelled) {
        setError(loadError.message);
        setLoading(false);
      }
    });

    return () => {
      cancelled = true;
    };
  }, [config.productsApi, deferredSearch, selectedCategory, page]);

  async function handleAddToCart(productId) {
    setMessage("");
    setError("");
    try {
      const addResponse = await fetch(config.cartAddApi, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({ product_id: productId, quantity: 1 }),
      });
      const payload = await readJson(addResponse);
      setCartSummary({ item_count: payload.item_count, subtotal: payload.subtotal });
      setMessage(payload.detail);
      const cartBadge = document.getElementById("cart-count-badge");
      if (cartBadge) {
        cartBadge.textContent = payload.item_count;
      }
    } catch (addError) {
      setError(addError.message);
    }
  }

  return (
    <div className="storefront-shell">
      <HeroCard
        selectedCategoryName={selectedCategoryName}
        productCount={catalog.count}
        cartSubtotal={cartSummary.subtotal}
      />
      <Filters
        categories={categories}
        selectedCategory={selectedCategory}
        setSelectedCategory={setSelectedCategory}
        searchInput={searchInput}
        setSearchInput={setSearchInput}
      />

      {message ? <div className="alert alert-success shadow-sm">{message}</div> : null}
      {error ? <div className="alert alert-danger shadow-sm">{error}</div> : null}

      {loading ? (
        <div className="card border-0 shadow-sm">
          <div className="card-body py-5 text-center text-secondary">Loading products...</div>
        </div>
      ) : catalog.results.length ? (
        <>
          <div className="row row-cols-1 row-cols-md-2 row-cols-xl-4 g-4">
            {catalog.results.map((product) => (
              <ProductCard key={product.id} product={product} onAddToCart={handleAddToCart} />
            ))}
          </div>
          <Pagination page={catalog.page} pages={catalog.pages} onPageChange={setPage} />
        </>
      ) : (
        <div className="card border-0 shadow-sm">
          <div className="card-body py-5 text-center">
            <h2 className="h4 mb-3">No products matched your search.</h2>
            <p className="text-secondary mb-0">Try a different keyword or switch back to all categories.</p>
          </div>
        </div>
      )}
    </div>
  );
}
