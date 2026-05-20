import { createRoot } from 'react-dom/client';

import { RouterProvider } from 'react-router-dom';

import { router } from '~app/router';

import '~styles/global-standalone.scss';

import { setup } from '@mpt-extension/sdk';

setup((element: Element) => {
  const root = createRoot(element);
  root.render(<RouterProvider router={router} />);
});
