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
        🛒
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
