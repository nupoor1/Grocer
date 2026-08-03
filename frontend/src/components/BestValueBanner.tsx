import { Link } from "react-router-dom";
import type { ProductResult } from "../api";

interface BestValue {
  unitLabel: string;
  pricePerUnit: number;
  merchant: string;
  productName: string;
  linkTo: string;
  imageUrl: string | null;
}

function escapeRegExp(s: string) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// The search grid tolerates loose substring matches (e.g. "milk" matching "Buttermilk")
// since it's just one extra card among many -- but this banner *asserts* a single winner,
// so a substring false-positive here (chicken breast as "best value milk") is much more
// damaging to trust. Require a whole-word match on the query before a result is eligible.
function matchesWholeWord(name: string, query: string) {
  const escaped = escapeRegExp(query.trim());
  if (!escaped) return true;
  return new RegExp(`\\b${escaped}\\b`, "i").test(name);
}

// Finds the single cheapest $/unit across every offer in every eligible result, one winner
// per unit dimension (100g and 100mL are never compared to each other -- that's meaningless).
// This deliberately spans different products/brands/sizes, unlike the per-product
// "Compare stores" view, so it's labeled accordingly rather than implied to be apples-to-apples.
function findBestValues(results: ProductResult[], query: string): BestValue[] {
  const best = new Map<string, BestValue>();

  for (const product of results) {
    if (!matchesWholeWord(product.name, query)) continue;
    for (const offer of product.offers) {
      if (offer.price_per_unit == null || offer.unit_label == null) continue;
      const current = best.get(offer.unit_label);
      if (!current || offer.price_per_unit < current.pricePerUnit) {
        best.set(offer.unit_label, {
          unitLabel: offer.unit_label,
          pricePerUnit: offer.price_per_unit,
          merchant: offer.merchant,
          productName: product.name,
          imageUrl: offer.image_url,
          linkTo:
            product.group_id != null
              ? `/item/group/${product.group_id}`
              : `/item/item/${offer.item_id}`,
        });
      }
    }
  }

  return [...best.values()].sort((a, b) => a.unitLabel.localeCompare(b.unitLabel));
}

export default function BestValueBanner({ results, query }: { results: ProductResult[]; query: string }) {
  const bestValues = findBestValues(results, query);
  if (bestValues.length === 0) return null;

  return (
    <div className="best-value-section">
      <div className="best-value-cards">
        {bestValues.map((bv) => (
          <Link
            key={bv.unitLabel}
            className="best-value-card"
            to={bv.linkTo}
            state={{ name: bv.productName, imageUrl: bv.imageUrl }}
          >
            <div className="best-value-label">Best value · per {bv.unitLabel}</div>
            <div className="best-value-price">${bv.pricePerUnit.toFixed(2)}</div>
            <div className="best-value-name">{bv.productName}</div>
            <div className="best-value-merchant">{bv.merchant}</div>
          </Link>
        ))}
      </div>
      <p className="best-value-caveat">
        Based on price per unit across different products/sizes in these results — not
        necessarily the same item at every store.
      </p>
    </div>
  );
}
