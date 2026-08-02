import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchCategories, type Category } from "../api";

// Capitalize for display only -- the underlying search_term stays lowercase,
// since that's what the API/DB actually stores and matches on.
function displayLabel(term: string) {
  return term.replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function CategoryChips() {
  const [categories, setCategories] = useState<Category[]>([]);

  useEffect(() => {
    fetchCategories()
      .then(setCategories)
      .catch(() => setCategories([]));
  }, []);

  if (categories.length === 0) return null;

  return (
    <div className="chip-row">
      {categories.map((c) => (
        <Link key={c.search_term} className="chip" to={`/search?q=${encodeURIComponent(c.search_term)}`}>
          {displayLabel(c.search_term)}
        </Link>
      ))}
    </div>
  );
}
