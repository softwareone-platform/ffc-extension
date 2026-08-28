import { useState } from 'react';

import { Select } from '@swo/design-system/select';

const OPTIONS = [
  { label: 'Contoso Cloud', value: 'org-contoso-cloud' },
  { label: 'Fabrikam FinOps', value: 'org-fabrikam-finops' },
  { label: 'Northwind Analytics', value: 'org-northwind-analytics' },
  { label: 'Adventure Works', value: 'org-adventure-works' },
  { label: 'Woodgrove Bank', value: 'org-woodgrove-bank' },
  { label: 'Litware Solutions', value: 'org-litware-solutions' },
  { label: 'Tailspin Toys', value: 'org-tailspin-toys' },
  { label: 'Proseware Systems', value: 'org-proseware-systems' },
  { label: 'Wingtip Consulting', value: 'org-wingtip-consulting' },
  { label: 'Trey Research', value: 'org-trey-research' },
  { label: 'Alpine Ski House', value: 'org-alpine-ski-house' },
  { label: 'Blue Yonder Airlines', value: 'org-blue-yonder-airlines' },
  { label: 'Coho Vineyard', value: 'org-coho-vineyard' },
  { label: 'Fourth Coffee', value: 'org-fourth-coffee' },
  { label: 'Graphic Design Institute', value: 'org-graphic-design-institute' },
  { label: 'Humongous Insurance', value: 'org-humongous-insurance' },
  { label: 'Lucerne Publishing', value: 'org-lucerne-publishing' },
  { label: 'Margie\'s Travel', value: 'org-margies-travel' },
  { label: 'School of Fine Art', value: 'org-school-of-fine-art' },
  { label: 'Southridge Video', value: 'org-southridge-video' },
  { label: 'Wide World Importers', value: 'org-wide-world-importers' },
  { label: 'Consolidated Messenger', value: 'org-consolidated-messenger' },
  { label: 'Baldwin Museum of Science', value: 'org-baldwin-museum' },
  { label: 'Bellows College', value: 'org-bellows-college' },
  { label: 'City Power & Light', value: 'org-city-power-and-light' },
  { label: 'Contoso Suites', value: 'org-contoso-suites' },
  { label: 'Munson\'s Pickles and Preserves', value: 'org-munsons-pickles' },
  { label: 'Relecloud Cargo', value: 'org-relecloud-cargo' },
  { label: 'Van Arsdel Ltd', value: 'org-van-arsdel' },
  { label: 'Tailwind Traders', value: 'org-tailwind-traders' },
  { label: 'Wingtip Holdings', value: 'org-wingtip-holdings' },
  { label: 'Woodgrove Financial', value: 'org-woodgrove-financial' },
  { label: 'Boreal Fabrication', value: 'org-boreal-fabrication' },
  { label: 'Aurora Analytics', value: 'org-aurora-analytics' },
  { label: 'Vertex Studios', value: 'org-vertex-studios' },
  { label: 'Meridian Holdings', value: 'org-meridian-holdings' },
  { label: 'Zephyr Labs', value: 'org-zephyr-labs' },
  { label: 'Cascade Retail', value: 'org-cascade-retail' },
  { label: 'Beacon Broadcasting', value: 'org-beacon-broadcasting' },
  { label: 'Cobalt Manufacturing', value: 'org-cobalt-manufacturing' },
  { label: 'Delta Payments', value: 'org-delta-payments' },
  { label: 'Ember Games', value: 'org-ember-games' },
  { label: 'Ferris Aerospace', value: 'org-ferris-aerospace' },
  { label: 'Granite State Fintech', value: 'org-granite-fintech' },
  { label: 'Horizon Media', value: 'org-horizon-media' },
  { label: 'Iron Peak Mining', value: 'org-iron-peak-mining' },
  { label: 'Juniper Networks Group', value: 'org-juniper-networks-group' },
  { label: 'Kestrel Aviation', value: 'org-kestrel-aviation' },
  { label: 'Larkspur Foods', value: 'org-larkspur-foods' },
  { label: 'Meadowlark Pharma', value: 'org-meadowlark-pharma' },
  { label: 'Nightingale Health', value: 'org-nightingale-health' },
  { label: 'Onyx Chemicals', value: 'org-onyx-chemicals' },
  { label: 'Pinnacle Ventures', value: 'org-pinnacle-ventures' },
  { label: 'Quartz Ceramics', value: 'org-quartz-ceramics' },
  { label: 'Redwood Timber Co', value: 'org-redwood-timber' },
  { label: 'Sable Motors', value: 'org-sable-motors' },
  { label: 'Terra Firma Realty', value: 'org-terra-firma-realty' },
  { label: 'Umbra Optics', value: 'org-umbra-optics' },
  { label: 'Verdant Farms', value: 'org-verdant-farms' },
  { label: 'Wildwood Outfitters', value: 'org-wildwood-outfitters' },
  { label: 'Xerxes Consulting', value: 'org-xerxes-consulting' },
  { label: 'Yarrow Botanicals', value: 'org-yarrow-botanicals' },
  { label: 'Zenith Robotics', value: 'org-zenith-robotics' },
  { label: 'Anchor Industries', value: 'org-anchor-industries' },
  { label: 'Beacon Analytics', value: 'org-beacon-analytics' },
  { label: 'Copperfield Holdings', value: 'org-copperfield-holdings' },
  { label: 'Driftwood Studios', value: 'org-driftwood-studios' },
  { label: 'Evergreen Utilities', value: 'org-evergreen-utilities' },
  { label: 'Falcon Freight', value: 'org-falcon-freight' },
  { label: 'Glacier Insurance', value: 'org-glacier-insurance' },
  { label: 'Hearthstone Realty', value: 'org-hearthstone-realty' },
  { label: 'Ivory Publishing', value: 'org-ivory-publishing' },
  { label: 'Jasper Diagnostics', value: 'org-jasper-diagnostics' },
  { label: 'Kelpie Marine', value: 'org-kelpie-marine' },
  { label: 'Lantern Media Group', value: 'org-lantern-media' },
  { label: 'Monarch Textiles', value: 'org-monarch-textiles' },
  { label: 'Nautilus Bearings', value: 'org-nautilus-bearings' },
  { label: 'Obsidian Systems', value: 'org-obsidian-systems' },
  { label: 'Polaris Shipping', value: 'org-polaris-shipping' },
  { label: 'Quicksilver Logistics', value: 'org-quicksilver-logistics' },
  { label: 'Riverstone Capital', value: 'org-riverstone-capital' },
];

export function OrganisationFilter() {
  const [selected, setSelected] = useState(OPTIONS[0].value);

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <strong>Selected organization</strong>
      <Select
        value={selected}
        options={OPTIONS}
        onChange={setSelected}
        maxHeight={320}
      />
    </div>
  );
}
