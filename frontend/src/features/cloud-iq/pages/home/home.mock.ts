import { IconName } from '@swo/design-system/icon';

import cottonbro from '~assets/pexels-cottonbro-6804068.jpg';
import eberhardgross from '~assets/pexels-eberhardgross-1287502.jpg';
import godiatima from '~assets/pexels-godiatima-4955393.jpg';
import thirdman from '~assets/pexels-thirdman-5257005.jpg';
import willianjusten from '~assets/pexels-willianjusten-35568053.jpg';

export type JumpBackInTile = {
  id: string;
  title: string;
  icon: IconName;
};

export type WhatsNewCard = {
  id: string;
  category: string;
  title: string;
  excerpt: string;
  image: string;
};

export const hero = {
  greeting: 'Hello, Demo',
  title: 'Activate Two Factor Authentication on your user account',
  body:
    'Please ensure that you have configured Two Factor Authentication on your Control Panel ' +
    'user account.\nThis is a mandatory Security Best Practice to prevent any unauthorized access.',
};

export const jumpBackIn: JumpBackInTile[] = [
  { id: 'manage-ms-accounts', title: 'Manage Microsoft Accounts', icon: 'tune' },
  { id: 'order-ms-csp', title: 'Order Microsoft CSP Products', icon: 'shopping_cart' },
  { id: 'software-catalog', title: 'Software Catalog', icon: 'category' },
  { id: 'service-provider-reporting', title: 'Service Provider Reporting', icon: 'assignment' },
  { id: 'create-support-request', title: 'Create Support Request', icon: 'contact_support' },
  { id: 'ms-csp-billing-analytics', title: 'Microsoft CSP Billing Analytics', icon: 'query_stats' },
];

export const whatsNew: WhatsNewCard[] = [
  {
    id: 'wn-1',
    category: 'Product update',
    title: 'New billing analytics dashboards',
    excerpt:
      'Explore refreshed Microsoft CSP billing analytics with drill-downs across subscriptions and tenants.',
    image: godiatima,
  },
  {
    id: 'wn-2',
    category: 'Announcement',
    title: 'Streamlined reseller onboarding',
    excerpt:
      'The reseller administration flow has been simplified to get your customers up and running faster.',
    image: eberhardgross,
  },
  {
    id: 'wn-3',
    category: 'Product update',
    title: 'New billing analytics dashboards',
    excerpt:
      'Explore refreshed Microsoft CSP billing analytics with drill-downs across subscriptions and tenants.',
    image: thirdman,
  },
  {
    id: 'wn-4',
    category: 'Announcement',
    title: 'Streamlined reseller onboarding',
    excerpt:
      'The reseller administration flow has been simplified to get your customers up and running faster.',
    image: cottonbro,
  },
  {
    id: 'wn-5',
    category: 'Product update',
    title: 'New billing analytics dashboards',
    excerpt:
      'Explore refreshed Microsoft CSP billing analytics with drill-downs across subscriptions and tenants.',
    image: willianjusten,
  },
  {
    id: 'wn-6',
    category: 'Announcement',
    title: 'Streamlined reseller onboarding',
    excerpt:
      'The reseller administration flow has been simplified to get your customers up and running faster.',
    image: godiatima,
  },
];
