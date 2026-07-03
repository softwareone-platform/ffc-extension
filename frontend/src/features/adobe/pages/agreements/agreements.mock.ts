export type Agreement = {
  id: string;
  name: string;
  agreementId: string;
  product: string;
  productId: string;
  licensee: string;
  licenseeId: string;
  isResale: boolean;
  buyer: string;
  buyerId: string;
  seller: string;
  sellerId: string;
  spxMonthly?: string;
  spxYearly?: string;
  createdAt: string;
  status: "Active" | "Terminated";
};

export const agreements: Agreement[] = [
  {
    id: "AGR-3476-8290-4143",
    name: "Adobe VIP Marketplace for Commercial",
    agreementId: "AGR-3476-8290-4143",
    product: "Adobe VIP Marketplace for Commercial",
    productId: "PRD-3427-4385",
    licensee: "Stark Marketing",
    licenseeId: "LCE-6723-0412-3548",
    isResale: false,
    buyer: "Stark Marketing",
    buyerId: "BUY-0293-7672",
    seller: "USA",
    sellerId: "SEL-9832 | US",
    createdAt: "2024-05-22T15:33:00",
    status: "Terminated",
  },
  {
    id: "AGR-3094-6209-0584",
    name: "Adobe VIP Marketplace for Education",
    agreementId: "AGR-3094-6209-0584",
    product: "Adobe VIP Marketplace for Education",
    productId: "PRD-0520-2723",
    licensee: "Stark University",
    licenseeId: "LCA-9692-1301-2848",
    isResale: true,
    buyer: "Stark University",
    buyerId: "BUY-2905-7320",
    seller: "USA",
    sellerId: "SEL-9832 | US",
    spxMonthly: "102,190.91 USD/month",
    spxYearly: "1,226,291.08 USD/year",
    createdAt: "2026-01-09T17:03:00",
    status: "Active",
  },
  {
    id: "AGR-9235-1011-4209",
    name: "Adobe VIP Marketplace for Government",
    agreementId: "AGR-9235-1011-4209",
    product: "Adobe VIP Marketplace for Commercial",
    productId: "PRD-3427-4385",
    licensee: "Stark Robotics",
    licenseeId: "LCE-2987-5692-8375",
    isResale: true,
    buyer: "Stark Robotics",
    buyerId: "BUY-0928-3509",
    seller: "USA",
    sellerId: "SEL-9832 | US",
    spxMonthly: "34,516.05 USD/month",
    spxYearly: "414,192.61 USD/year",
    createdAt: "2024-12-17T19:10:00",
    status: "Active",
  },
  {
    id: "AGR-9304-7689-8274",
    name: "Adobe VIP Marketplace for Large Government Agencies",
    agreementId: "AGR-9304-7689-8274",
    product: "Adobe VIP Marketplace for Government",
    productId: "PRD-3961-2846",
    licensee: "Stark Defense",
    licenseeId: "LCE-1985-7243-9867",
    isResale: false,
    buyer: "Stark Defense Projects",
    buyerId: "BUY-4578-6394",
    seller: "USA",
    sellerId: "SEL-9832 | US",
    spxMonthly: "49,442.16 USD/month",
    spxYearly: "593,305.94 USD/year",
    createdAt: "2025-08-12T19:31:00",
    status: "Active",
  },
];
