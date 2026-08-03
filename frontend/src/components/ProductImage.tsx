import { useState } from "react";

interface Props {
  src: string | null;
  alt: string;
}

// Flipp's image URLs occasionally 404 or the item may never have had one --
// fall back to a simple placeholder rather than showing a broken-image icon.
export default function ProductImage({ src, alt }: Props) {
  const [failed, setFailed] = useState(false);

  if (!src || failed) {
    return (
      <div className="product-image product-image-placeholder" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" width="40%" height="40%">
          <rect x="2" y="4" width="20" height="16" rx="2" stroke="currentColor" strokeWidth="1.5" />
          <circle cx="8" cy="10" r="1.75" stroke="currentColor" strokeWidth="1.5" />
          <path
            d="M4 17l5-5 3.5 3.5L16.5 11 20 15"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>
    );
  }

  return (
    <img
      className="product-image"
      src={src}
      alt={alt}
      loading="lazy"
      onError={() => setFailed(true)}
    />
  );
}
