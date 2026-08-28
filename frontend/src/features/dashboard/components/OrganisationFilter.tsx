import { useMemo, useState } from "react";

import { Button } from "@swo/design-system/button";
import { Dropdown } from "@swo/design-system/dropdown";
import { Input } from "@swo/design-system/input";

const ORGANIZATIONS = [
  { id: "org-contoso-cloud", name: "Contoso Cloud" },
  { id: "org-fabrikam-finops", name: "Fabrikam FinOps" },
  { id: "org-northwind-analytics", name: "Northwind Analytics" },
  { id: "org-adventure-works", name: "Adventure Works" },
  { id: "org-woodgrove-bank", name: "Woodgrove Bank" },
  { id: "org-litware-solutions", name: "Litware Solutions" },
  { id: "org-tailspin-toys", name: "Tailspin Toys" },
  { id: "org-proseware-systems", name: "Proseware Systems" },
  { id: "org-wingtip-consulting", name: "Wingtip Consulting" },
  { id: "org-trey-research", name: "Trey Research" },
  { id: "org-alpine-ski-house", name: "Alpine Ski House" },
  { id: "org-blue-yonder-airlines", name: "Blue Yonder Airlines" },
  { id: "org-coho-vineyard", name: "Coho Vineyard" },
  { id: "org-fourth-coffee", name: "Fourth Coffee" },
  { id: "org-graphic-design-institute", name: "Graphic Design Institute" },
  { id: "org-humongous-insurance", name: "Humongous Insurance" },
  { id: "org-lucerne-publishing", name: "Lucerne Publishing" },
  { id: "org-margies-travel", name: "Margie's Travel" },
  { id: "org-school-of-fine-art", name: "School of Fine Art" },
  { id: "org-southridge-video", name: "Southridge Video" },
  { id: "org-wide-world-importers", name: "Wide World Importers" },
  { id: "org-consolidated-messenger", name: "Consolidated Messenger" },
  { id: "org-baldwin-museum", name: "Baldwin Museum of Science" },
  { id: "org-bellows-college", name: "Bellows College" },
  { id: "org-city-power-and-light", name: "City Power & Light" },
  { id: "org-contoso-suites", name: "Contoso Suites" },
  { id: "org-munsons-pickles", name: "Munson's Pickles and Preserves" },
  { id: "org-relecloud-cargo", name: "Relecloud Cargo" },
  { id: "org-van-arsdel", name: "Van Arsdel Ltd" },
  { id: "org-tailwind-traders", name: "Tailwind Traders" },
  { id: "org-wingtip-holdings", name: "Wingtip Holdings" },
  { id: "org-woodgrove-financial", name: "Woodgrove Financial" },
  { id: "org-boreal-fabrication", name: "Boreal Fabrication" },
  { id: "org-aurora-analytics", name: "Aurora Analytics" },
  { id: "org-vertex-studios", name: "Vertex Studios" },
  { id: "org-meridian-holdings", name: "Meridian Holdings" },
  { id: "org-zephyr-labs", name: "Zephyr Labs" },
  { id: "org-cascade-retail", name: "Cascade Retail" },
  { id: "org-beacon-broadcasting", name: "Beacon Broadcasting" },
  { id: "org-cobalt-manufacturing", name: "Cobalt Manufacturing" },
  { id: "org-delta-payments", name: "Delta Payments" },
  { id: "org-ember-games", name: "Ember Games" },
  { id: "org-ferris-aerospace", name: "Ferris Aerospace" },
  { id: "org-granite-fintech", name: "Granite State Fintech" },
  { id: "org-horizon-media", name: "Horizon Media" },
  { id: "org-iron-peak-mining", name: "Iron Peak Mining" },
  { id: "org-juniper-networks-group", name: "Juniper Networks Group" },
  { id: "org-kestrel-aviation", name: "Kestrel Aviation" },
  { id: "org-larkspur-foods", name: "Larkspur Foods" },
  { id: "org-meadowlark-pharma", name: "Meadowlark Pharma" },
  { id: "org-nightingale-health", name: "Nightingale Health" },
  { id: "org-onyx-chemicals", name: "Onyx Chemicals" },
  { id: "org-pinnacle-ventures", name: "Pinnacle Ventures" },
  { id: "org-quartz-ceramics", name: "Quartz Ceramics" },
  { id: "org-redwood-timber", name: "Redwood Timber Co" },
  { id: "org-sable-motors", name: "Sable Motors" },
  { id: "org-terra-firma-realty", name: "Terra Firma Realty" },
  { id: "org-umbra-optics", name: "Umbra Optics" },
  { id: "org-verdant-farms", name: "Verdant Farms" },
  { id: "org-wildwood-outfitters", name: "Wildwood Outfitters" },
  { id: "org-xerxes-consulting", name: "Xerxes Consulting" },
  { id: "org-yarrow-botanicals", name: "Yarrow Botanicals" },
  { id: "org-zenith-robotics", name: "Zenith Robotics" },
  { id: "org-anchor-industries", name: "Anchor Industries" },
  { id: "org-beacon-analytics", name: "Beacon Analytics" },
  { id: "org-copperfield-holdings", name: "Copperfield Holdings" },
  { id: "org-driftwood-studios", name: "Driftwood Studios" },
  { id: "org-evergreen-utilities", name: "Evergreen Utilities" },
  { id: "org-falcon-freight", name: "Falcon Freight" },
  { id: "org-glacier-insurance", name: "Glacier Insurance" },
  { id: "org-hearthstone-realty", name: "Hearthstone Realty" },
  { id: "org-ivory-publishing", name: "Ivory Publishing" },
  { id: "org-jasper-diagnostics", name: "Jasper Diagnostics" },
  { id: "org-kelpie-marine", name: "Kelpie Marine" },
  { id: "org-lantern-media", name: "Lantern Media Group" },
  { id: "org-monarch-textiles", name: "Monarch Textiles" },
  { id: "org-nautilus-bearings", name: "Nautilus Bearings" },
  { id: "org-obsidian-systems", name: "Obsidian Systems" },
  { id: "org-polaris-shipping", name: "Polaris Shipping" },
  { id: "org-quicksilver-logistics", name: "Quicksilver Logistics" },
  { id: "org-riverstone-capital", name: "Riverstone Capital" },
];

const OPTIONS = ORGANIZATIONS.map((organization) => ({
  value: organization.id,
  label: organization.name,
}));

export function OrganisationFilter() {
  const [selected, setSelected] = useState(ORGANIZATIONS[0].id);
  const [search, setSearch] = useState("");

  const filteredOptions = useMemo(() => {
    const needle = search.trim().toLowerCase();
    if (!needle) return OPTIONS;
    return OPTIONS.filter((option) => option.label.toLowerCase().includes(needle));
  }, [search]);

  const selectedLabel =
    ORGANIZATIONS.find((organization) => organization.id === selected)?.name ??
    ORGANIZATIONS[0].name;

  return (
    <>
      <span className={"ffc-tabbar__label"}>Selected organization</span>
      <Dropdown
        value={selected}
        options={filteredOptions}
        onItemSelected={setSelected}
        maxHeight={320}
        positions={[{ position: "bottom-end" }]}
        className={"ffc-org-dropdown"}
        headerContent={
          <Input
            value={search}
            onChange={(event) => setSearch((event.target as HTMLInputElement).value)}
            placeholder={"Search organizations…"}
          />
        }
      >
        <Button type={"outline"}>{selectedLabel}</Button>
      </Dropdown>
    </>
  );
}
