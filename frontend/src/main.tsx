import { pdfjs } from "react-pdf";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();
import React from "react";
import ReactDOM from "react-dom/client";

import App from "./app/App";
import { useAuthStore } from "./stores/auth.store";

import "./styles/design-system.css";

useAuthStore.setState({
  isInitialized: true,
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
