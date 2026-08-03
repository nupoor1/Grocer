import { Link } from "react-router-dom";
import ProductImage from "./ProductImage";
import DealSignals from "./DealSignals";

interface Props {
  name: string;
  merchant: string;
  currentPrice: number;
  originalPrice: number | null;
  imageUrl: string | null;
  discountPct: number | null;
  vsOwnHistoryPct: number | null;
  vsStatcanPct: number | null;
  storeCount: number;
  linkTo: string;
}

export default function ProductCard({
  name,
  merchant,
  currentPrice,
  originalPrice,
  imageUrl,
  discountPct,
  vsOwnHistoryPct,
  vsStatcanPct,
  storeCount,
  linkTo,
}: Props) {
  return (
    <Link className="product-tile" to={linkTo} state={{ name, imageUrl }}>
      <div className="product-tile-image-wrap">
        <ProductImage src={imageUrl} alt={name} />
        {discountPct !== null && <span className="discount-badge">-{Math.round(discountPct)}%</span>}
      </div>
      <div className="product-tile-body">
        <div className="product-tile-name">{name}</div>
        <div className="product-tile-merchant">{merchant}</div>
        <div className="product-tile-price">
          ${currentPrice.toFixed(2)}
          {originalPrice != null && originalPrice > currentPrice && (
            <span className="deal-was"> ${originalPrice.toFixed(2)}</span>
          )}
        </div>
        <DealSignals
          discountPct={discountPct}
          vsOwnHistoryPct={vsOwnHistoryPct}
          vsStatcanPct={vsStatcanPct}
          compact
        />
        {storeCount > 1 && <div className="compare-badge">Compare {storeCount} stores →</div>}
      </div>
    </Link>
  );
}
