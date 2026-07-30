import { useMemo } from "react";

import {
  GridCellDateTime,
  GridCellSimple,
  GridCellStatus,
  GridCellTitleSubtitle,
  GridColumnDefinition,
  GridInMemoryConfig,
  useGridInMemory,
} from "@swo/design-system/grid";

import { AdobeIcon, SellerFlagIcon } from "~features/sandboxStandalone/icons";

import { Agreement, agreements } from "./agreements.mock";

function renderTitleLink({ href, label }: { href: string; label: string }) {
  // The portal embeds this extension in a sandboxed iframe without `allow-popups`,
  // so `_blank` is popup-blocked. Navigate the top-level tab instead.
  return (
    <a className="adobe-agreements__link" href={href} target="_top" rel="noopener noreferrer">
      {label}
    </a>
  );
}

function useColumns(): GridColumnDefinition<Agreement>[] {
  return useMemo(
    () => [
      {
        name: "name",
        title: "Name",
        cell: (item: Agreement) => (
          <GridCellTitleSubtitle
            title={renderTitleLink({ href: "https://www.softwareone.com", label: item.name })}
            subtitle={item.agreementId}
          />
        ),
        initialWidth: 220,
      },
      {
        name: "product",
        title: "Product",
        cell: (item: Agreement) => (
          <div className="adobe-agreements__product">
            <AdobeIcon className="adobe-agreements__product-icon" width={32} />
            <GridCellTitleSubtitle
              title={renderTitleLink({ href: "https://www.softwareone.com", label: item.product })}
              subtitle={item.productId}
            />
          </div>
        ),
        initialWidth: 220,
      },
      {
        name: "licensee",
        title: "Licensee",
        cell: (item: Agreement) => (
          <GridCellTitleSubtitle
            title={renderTitleLink({ href: "https://www.google.com", label: item.licensee })}
            subtitle={item.licenseeId}
          />
        ),
        initialWidth: 200,
      },
      {
        name: "resale",
        title: "Resale",
        cell: (item: Agreement) => (
          <GridCellStatus
            status={item.isResale ? "success" : "error"}
            label={item.isResale ? "Yes" : "No"}
          />
        ),
        initialWidth: 120,
      },
      {
        name: "buyer",
        title: "Buyer",
        cell: (item: Agreement) => (
          <GridCellTitleSubtitle
            title={renderTitleLink({ href: "https://www.yahoo.com", label: item.buyer })}
            subtitle={item.buyerId}
          />
        ),
        initialWidth: 200,
      },
      {
        name: "seller",
        title: "Seller",
        cell: (item: Agreement) => (
          <div className="adobe-agreements__seller">
            <SellerFlagIcon
              className="adobe-agreements__seller-icon"
              rounded={true}
              width={24}
              height={24}
            />
            <GridCellTitleSubtitle title={item.seller} subtitle={item.sellerId} />
          </div>
        ),
        initialWidth: 180,
      },
      {
        name: "spx",
        title: "SPx",
        cell: (item: Agreement) =>
          item.spxMonthly ? (
            <GridCellTitleSubtitle title={item.spxMonthly} subtitle={item.spxYearly} />
          ) : (
            <GridCellSimple>—</GridCellSimple>
          ),
        initialWidth: 200,
      },
      {
        name: "created",
        title: "Created",
        cell: (item: Agreement) => <GridCellDateTime date={item.createdAt} />,
        initialWidth: 150,
      },
      {
        name: "status",
        type: "Status",
        title: "Status",
        cell: (item: Agreement) => (
          <GridCellStatus
            status={item.status === "Active" ? "success" : "error"}
            label={item.status}
          />
        ),
        initialWidth: 130,
      },
    ],
    [],
  );
}

export function useGridConfig() {
  const columns = useColumns();

  const config = useMemo(
    (): GridInMemoryConfig<Agreement> => ({
      id: "grid__adobe-agreements",
      columns,
    }),
    [columns],
  );

  return useGridInMemory<Agreement>(agreements, config);
}
