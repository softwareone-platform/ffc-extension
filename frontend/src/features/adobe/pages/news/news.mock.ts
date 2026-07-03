export type NewsMessage = {
  id: string;
  meta: string;
  title: string;
  intro: string;
  bulletsTitle?: string;
  bullets: { lead?: string; text: string }[];
  link: string;
};

export const messages: NewsMessage[] = [
  {
    id: "release-2026-04-07",
    meta: "Adobe news · 7 Apr 2026 08:42",
    title: "Release date: 7 Apr 2026",
    intro: "Our latest release brings some quality of life improvements to your Adobe experience.",
    bullets: [
      {
        lead: "Clearer and more intuitive ordering experience:",
        text: "we've refined how Adobe products are presented throughout the SoftwareOne Marketplace including clearer product descriptions and improved guidance during ordering.",
      },
      {
        lead: "More transparency during reseller transfers:",
        text: "view the items and pricing of the subscriptions you are transferring to SoftwareOne.",
      },
      {
        lead: "Keep track of your 3-year commitments:",
        text: "receive notifications as your commitments come to an end with the option to start a new commitment.",
      },
      {
        lead: "Better visibility of your linked memberships:",
        text: "your linked membership details are now visible directly within your agreement.",
      },
    ],
    link: "https://docs.platform.softwareone.com/extensions/adobe-vip-marketplace/release-notes",
  },
  {
    id: "managing-licenses",
    meta: "Adobe news · 14 May 2026 18:45",
    title: "Managing Your Adobe Licenses",
    intro:
      "In this video, we will guide you through the process of managing your Adobe licenses via the Marketplace. You'll learn how to change the quantities of your existing licenses and add new products seamlessly.",
    bulletsTitle: "What You'll Learn:",
    bullets: [
      {
        text: "How to navigate to your subscriptions and place orders for single or multiple subscriptions.",
      },
      { text: "Steps to adjust subscription quantities and add tracking information." },
      { text: "How to terminate a subscription and understand the implications." },
      { text: "Tips for reviewing your order summary and estimating financial impacts." },
    ],
    link: "https://docs.platform.softwareone.com/extensions/adobe-vip-marketplace/tutorials-and-videos",
  },
];
