import "bootstrap/dist/css/bootstrap.min.css";
import "./storefront.css";
import React from "react";
import { createRoot } from "react-dom/client";

import { StorefrontApp } from "./storefront";

const rootElement = document.getElementById("storefront-root");
const configElement = document.getElementById("storefront-config");

if (rootElement && configElement) {
  const config = JSON.parse(configElement.textContent || "{}");
  createRoot(rootElement).render(
    <React.StrictMode>
      <StorefrontApp config={config} />
    </React.StrictMode>,
  );
}
