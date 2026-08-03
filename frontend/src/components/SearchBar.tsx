import { useEffect, useState, type FormEvent } from "react";
import { useNavigate, useSearchParams, useLocation } from "react-router-dom";

// Lives in the persistent top bar, present on every route -- submitting always
// routes to /search?q=..., regardless of which page you were on when you typed.
export default function SearchBar() {
  const navigate = useNavigate();
  const location = useLocation();
  const [params] = useSearchParams();
  const [q, setQ] = useState(params.get("q") ?? "");

  // keep the field in sync with the URL on /search (e.g. a category chip link),
  // and clear it whenever navigating away to any other page
  useEffect(() => {
    setQ(location.pathname === "/search" ? params.get("q") ?? "" : "");
  }, [location.pathname, params]);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!q.trim()) return;
    navigate(`/search?q=${encodeURIComponent(q.trim())}`);
  }

  return (
    <form onSubmit={handleSubmit} className="top-search-form">
      <svg className="top-search-icon" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="2" />
        <line x1="21" y1="21" x2="16.65" y2="16.65" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </svg>
      <input
        type="search"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="Search groceries..."
      />
    </form>
  );
}
