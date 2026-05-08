import { createRoot } from 'react-dom/client';
import { RouterProvider } from 'react-router-dom';
import { setup } from '@mpt-extension/sdk';
import { router } from '~app/router';
import '~styles/global.scss';

setup((element: Element) => {
    const root = createRoot(element);
    root.render(<RouterProvider router={router} />);
});
