import React, { startTransition, useDeferredValue, useEffect, useMemo, useState } from "react";

const currencyFormatter = new Intl.NumberFormat("en-PH", {
  style: "currency",
  currency: "PHP",
});

const promoNotes = [
  {
    label: "Picked this week",
    title: "Bright market arrivals",
    copy: "Soft cards, playful greens, and cleaner spacing make the catalog feel lighter to browse.",
  },
  {
    label: "Weekend stock-up",
    title: "Colorful pantry staples",
    copy: "Live product imagery now does the heavy lifting, so the page feels fresh without losing utility.",
  },
  {
    label: "Neighborhood favorite",
    title: "Easy add-to-cart flow",
    copy: "Rounded edges and clear calls to action keep shopping warm, simple, and easy to trust.",
  },
];

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

function getInitials(text) {
  return (
    text
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase() || "")
      .join("") || "FM"
  );
}

function truncateWords(text, limit = 16) {
  const words = (text || "").trim().split(/\s+/).filter(Boolean);
  if (!words.length) {
    return "Fresh, thoughtful essentials for everyday homes.";
  }
  if (words.length <= limit) {
    return words.join(" ");
  }
  return `${words.slice(0, limit).join(" ")}...`;
}

function VisualTile({ product, className, label }) {
  return (
    <div className={`hero-fruit ${className}`}>
      {product?.image_url ? (
        <img src={product.image_url} alt={product.name} className="hero-fruit__image" />
      ) : (
        <div className="hero-fruit__fallback">
          <span className="hero-fruit__fallback-mark">{getInitials(label)}</span>
          <span className="hero-fruit__fallback-label">{label}</span>
        </div>
      )}
    </div>
  );
}

function HeroVisual({ products }) {
  const [primary, secondary, tertiary] = products;

  return (
    <div className="market-hero__visual" aria-hidden="true">
      <div className="hero-orb hero-orb--green" />
      <div className="hero-orb hero-orb--mist" />
      <VisualTile product={primary} className="hero-fruit--primary" label={primary?.name || "Seasonal Picks"} />
      <VisualTile product={secondary} className="hero-fruit--secondary" label={secondary?.name || "Market Goods"} />
      <VisualTile product={tertiary} className="hero-fruit--tertiary" label={tertiary?.name || "Daily Finds"} />
    </div>
  );
}

function HeroCard({
  selectedCategoryName,
  productCount,
  cartSubtotal,
  categoryCount,
  products,
  hasActiveFilters,
  onResetFilters,
}) {
  return (
    <section className="market-hero">
      <div className="market-hero__content">
        <span className="section-kicker">Organic market theme</span>
        <h1 className="market-hero__title">
          Farm Fresh Organic <span>Finds.</span>
        </h1>
        <p className="market-hero__copy">
          A brighter, produce-inspired storefront for everyday shopping.{" "}
          {selectedCategoryName
            ? `You're currently browsing ${selectedCategoryName.toLowerCase()}.`
            : "Browse every aisle or jump straight to the essentials you need next."}
        </p>
        <div className="hero-actions">
          <a href="#catalog-grid" className="btn btn-success">
            Shop Collection
          </a>
          {hasActiveFilters ? (
            <button type="button" className="btn btn-outline-success" onClick={onResetFilters}>
              Clear Filters
            </button>
          ) : (
            <a href="#category-grid" className="btn btn-outline-success">
              Browse Aisles
            </a>
          )}
        </div>
        <div className="hero-metrics">
          <div className="hero-metric">
            <strong>{productCount}</strong>
            <span>available picks</span>
          </div>
          <div className="hero-metric">
            <strong>{categoryCount}</strong>
            <span>live categories</span>
          </div>
          <div className="hero-metric">
            <strong>{currencyFormatter.format(Number(cartSubtotal || 0))}</strong>
            <span>cart subtotal</span>
          </div>
        </div>
      </div>
      <HeroVisual products={products} />
    </section>
  );
}

function PromoCard({ product, note, index }) {
  return (
    <article className={`promo-card promo-card--${["mint", "peach", "sage"][index % 3]}`}>
      <div className="promo-card__copy">
        <span className="promo-card__eyebrow">{note.label}</span>
        <h2>{product?.category_name || note.title}</h2>
        <p>{product ? truncateWords(product.description, 11) : note.copy}</p>
        {product ? (
          <a href={product.detail_url} className="promo-card__link">
            See pick
          </a>
        ) : (
          <span className="promo-card__link">Fresh style</span>
        )}
      </div>
      <div className="promo-card__thumb">
        {product?.image_url ? (
          <img src={product.image_url} alt={product.name} className="promo-card__image" />
        ) : (
          <span className="promo-card__thumb-mark">{getInitials(product?.category_name || note.title)}</span>
        )}
      </div>
    </article>
  );
}

function PromoStrip({ products }) {
  return (
    <section className="promo-strip">
      {promoNotes.map((note, index) => (
        <PromoCard key={note.label} product={products[index]} note={note} index={index} />
      ))}
    </section>
  );
}

function CategoryShelf({ categories, selectedCategory, setSelectedCategory }) {
  const totalProducts = categories.reduce((total, category) => total + category.product_count, 0);

  if (!categories.length) {
    return null;
  }

  return (
    <section className="category-section" id="category-grid">
      <div className="section-heading">
        <div>
          <span className="section-kicker">Top categories</span>
          <h2 className="section-title">Shop by aisle</h2>
        </div>
        <p className="section-copy">Quick category cards keep the catalog easy to scan on both desktop and mobile.</p>
      </div>
      <div className="category-shelf">
        <button
          type="button"
          className={`category-card tone-green ${selectedCategory ? "" : "is-active"}`}
          onClick={() => setSelectedCategory("")}
        >
          <span className="category-card__mark">ALL</span>
          <strong>All products</strong>
          <span className="category-card__count">{totalProducts} items</span>
        </button>
        {categories.map((category, index) => (
          <button
            key={category.id}
            type="button"
            className={`category-card tone-${["green", "mist", "orange", "sand"][index % 4]} ${
              selectedCategory === category.slug ? "is-active" : ""
            }`}
            onClick={() => setSelectedCategory(category.slug)}
          >
            <span className="category-card__mark">{getInitials(category.name)}</span>
            <strong>{category.name}</strong>
            <span className="category-card__count">{category.product_count} items</span>
          </button>
        ))}
      </div>
    </section>
  );
}

function Filters({
  categories,
  selectedCategory,
  setSelectedCategory,
  searchInput,
  setSearchInput,
  productCount,
}) {
  return (
    <section className="filter-panel">
      <div className="filter-panel__copy">
        <span className="section-kicker">Curated catalog</span>
        <h2 className="section-title">Find what you need fast</h2>
        <p className="section-copy">
          Search the storefront, switch categories, and keep the shopping flow light even as the live data changes.
        </p>
      </div>
      <div className="filter-panel__controls">
        <label className="filter-control" htmlFor="storefront-search">
          <span className="filter-control__label">Search products</span>
          <input
            id="storefront-search"
            className="form-control form-control-lg"
            placeholder="Try greens, snacks, coffee, tote..."
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
          />
        </label>
        <label className="filter-control" htmlFor="storefront-category">
          <span className="filter-control__label">Filter by category</span>
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
        </label>
        <div className="filter-summary">
          <span className="filter-summary__count">{productCount}</span>
          <span className="filter-summary__label">{productCount === 1 ? "product visible" : "products visible"}</span>
        </div>
      </div>
    </section>
  );
}

function BannerImage({ product, fallbackLabel }) {
  return (
    <div className="wide-banner__image">
      {product?.image_url ? (
        <img src={product.image_url} alt={product.name} className="wide-banner__photo" />
      ) : (
        <div className="wide-banner__fallback">
          <span>{getInitials(fallbackLabel)}</span>
        </div>
      )}
    </div>
  );
}

function FeatureBanners({ products }) {
  const primary = products[0];
  const secondary = products[1] || products[0];

  if (!primary && !secondary) {
    return null;
  }

  return (
    <section className="banner-grid">
      <article className="wide-banner wide-banner--soft">
        <div className="wide-banner__copy">
          <span className="section-kicker">Fresh picks</span>
          <h2>Build a brighter basket for the week</h2>
          <p>From pantry staples to home comforts, the new layout makes every product feel cleaner and easier to spot.</p>
          {primary ? (
            <a href={primary.detail_url} className="wide-banner__link">
              Explore {primary.category_name}
            </a>
          ) : null}
        </div>
        <BannerImage product={primary} fallbackLabel="Fresh Goods" />
      </article>
      <article className="wide-banner wide-banner--deep">
        <div className="wide-banner__copy">
          <span className="section-kicker section-kicker--light">Weekly highlight</span>
          <h2>Restock without the visual clutter</h2>
          <p>Rounded blocks, softer neutrals, and green accents keep the page warm while the catalog stays practical.</p>
          {secondary ? (
            <a href={secondary.detail_url} className="wide-banner__link wide-banner__link--light">
              See {secondary.name}
            </a>
          ) : null}
        </div>
        <BannerImage product={secondary} fallbackLabel="Garden Picks" />
      </article>
    </section>
  );
}

function ProductCard({ product, onAddToCart, index }) {
  const hasRating = Boolean(product.avg_rating && Number(product.avg_rating) > 0);

  return (
    <article className="col">
      <div className={`product-card tone-${["green", "mist", "orange", "sand"][index % 4]}`}>
        <a href={product.detail_url} className="product-card__media text-decoration-none">
          {product.image_url ? (
            <img src={product.image_url} className="product-image" alt={product.name} />
          ) : (
            <div className="product-image product-image-placeholder d-flex align-items-center justify-content-center">
              No image yet
            </div>
          )}
        </a>
        <div className="product-card__body">
          <div className="product-card__topline">
            <span className="product-card__category">{product.category_name}</span>
            <span className="product-card__rating">
              {hasRating ? `${Number(product.avg_rating).toFixed(1)} / 5` : "Fresh drop"}
            </span>
          </div>
          <h2 className="product-card__title">
            <a href={product.detail_url} className="text-decoration-none text-reset">
              {product.name}
            </a>
          </h2>
          <p className="product-card__description">{truncateWords(product.description, 18)}</p>
          <div className="product-card__bottom">
            <div>
              <strong className="product-card__price">{currencyFormatter.format(Number(product.price))}</strong>
              <span className={`product-stock ${product.stock > 0 ? "is-available" : "is-sold-out"}`}>
                {product.stock > 0 ? `${product.stock} in stock` : "Out of stock"}
              </span>
            </div>
            <button
              type="button"
              className="btn btn-success product-card__button"
              disabled={product.stock < 1}
              onClick={() => onAddToCart(product.id)}
            >
              Add to cart
            </button>
          </div>
        </div>
      </div>
    </article>
  );
}

function LoadingCatalog() {
  return (
    <div className="row row-cols-1 row-cols-md-2 row-cols-xl-4 g-4">
      {Array.from({ length: 4 }, (_, index) => (
        <div className="col" key={`skeleton-${index}`}>
          <div className="product-card product-card--skeleton">
            <div className="product-skeleton product-skeleton__image" />
            <div className="product-card__body">
              <div className="product-skeleton product-skeleton__line product-skeleton__line--short" />
              <div className="product-skeleton product-skeleton__line" />
              <div className="product-skeleton product-skeleton__line" />
              <div className="product-skeleton product-skeleton__line product-skeleton__line--tiny" />
            </div>
          </div>
        </div>
      ))}
    </div>
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
    <nav aria-label="Storefront pages" className="pagination-wrap">
      <ul className="pagination pagination-lg storefront-pagination flex-wrap">
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
  const heroProducts = useMemo(
    () => catalog.results.filter((product) => product.image_url).slice(0, 3),
    [catalog.results],
  );
  const promoProducts = useMemo(() => catalog.results.slice(0, 3), [catalog.results]);
  const bannerProducts = useMemo(
    () => catalog.results.filter((product) => product.image_url).slice(0, 2),
    [catalog.results],
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

  function handleResetFilters() {
    startTransition(() => {
      setSearchInput("");
      setSelectedCategory("");
      setPage(1);
    });
  }

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
        categoryCount={categories.length}
        products={heroProducts}
        hasActiveFilters={Boolean(searchInput.trim() || selectedCategory)}
        onResetFilters={handleResetFilters}
      />
      <PromoStrip products={promoProducts} />
      <CategoryShelf
        categories={categories}
        selectedCategory={selectedCategory}
        setSelectedCategory={setSelectedCategory}
      />
      <Filters
        categories={categories}
        selectedCategory={selectedCategory}
        setSelectedCategory={setSelectedCategory}
        searchInput={searchInput}
        setSearchInput={setSearchInput}
        productCount={catalog.count}
      />

      {message ? <div className="alert alert-success shadow-sm">{message}</div> : null}
      {error ? <div className="alert alert-danger shadow-sm">{error}</div> : null}

      <FeatureBanners products={bannerProducts} />

      <section className="catalog-section" id="catalog-grid">
        <div className="section-heading">
          <div>
            <span className="section-kicker">Featured products</span>
            <h2 className="section-title">Fresh picks from the catalog</h2>
          </div>
          <p className="section-copy">
            Browse real inventory in a softer grocery-inspired layout, with search, filters, and cart actions still
            fully wired to Django.
          </p>
        </div>

        {loading ? (
          <LoadingCatalog />
        ) : catalog.results.length ? (
          <>
            <div className="row row-cols-1 row-cols-md-2 row-cols-xl-4 g-4">
              {catalog.results.map((product, index) => (
                <ProductCard key={product.id} product={product} onAddToCart={handleAddToCart} index={index} />
              ))}
            </div>
            <Pagination page={catalog.page} pages={catalog.pages} onPageChange={setPage} />
          </>
        ) : (
          <div className="empty-state">
            <h2 className="h4 mb-3">No products matched your search.</h2>
            <p className="mb-0">Try a different keyword or switch back to all categories for more fresh picks.</p>
          </div>
        )}
      </section>
    </div>
  );
}
