import { BoldText, RegularText } from "@swo/design-system/text";
import { Tiles } from "@swo/design-system/tiles";

import { AdobeIcon } from "~features/adobe/icons";

import { products } from "./products.mock";

import "./ProductsPage.scss";

export function ProductsPage() {
  return (
    <div className="adobe-products">
      <header className="adobe-products__header">
        <AdobeIcon className="adobe-products__icon" />
        <div className="adobe-products__header-text">
          <BoldText size={4}>Adobe</BoldText>
          <RegularText size={1} color="grey-5">
            ACC-1221-2574
          </RegularText>
        </div>
      </header>

      <Tiles className="adobe-products__tiles">
        {products.map((product) => (
          <Tiles.Tile
            key={product.id}
            url="#"
            title={product.name}
            subtitle={product.id}
            subHeading={undefined}
            body={product.description}
            icon={<AdobeIcon className="adobe-products__icon" />}
            badgeConfig={product.isFeatured ? { label: "Featured", icon: "done" } : undefined}
          />
        ))}
      </Tiles>
    </div>
  );
}
