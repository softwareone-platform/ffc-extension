export type Product = {
  id: string;
  name: string;
  description: string;
  isFeatured?: boolean;
};

export const products: Product[] = [
  {
    id: "PRD-3427-4385",
    name: "Adobe VIP Marketplace for Commercial",
    description:
      "Access Adobe's industry-leading creative and document solutions through SoftwareOne — with flexible purchasing, centralized billing, and simple subscription management for your organization.",
    isFeatured: true,
  },
  {
    id: "PRD-0520-2723",
    name: "Adobe VIP Marketplace for Education",
    description: "The creative resource for K–12 and higher education.",
  },
  {
    id: "PRD-3961-2846",
    name: "Adobe VIP Marketplace for Government",
    description:
      "Create simple, seamless, and secure government experiences. We provide government agencies with the solutions they need to modernize digital experiences, efficiently deliver services, increase citizen engagement.",
  },
  {
    id: "PRD-0049-1462",
    name: "Adobe VIP Marketplace for Large Government Agencies",
    description:
      "Adobe's ground-breaking innovations empower everyone, everywhere to imagine, create, and bring any digital experience to life.",
  },
];
