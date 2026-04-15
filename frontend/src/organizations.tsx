import React from 'react';
import { createRoot } from 'react-dom/client';
import { setup } from '@mpt-extension/sdk';
import Organizations from './modules/Organizations/index';

setup((element: Element) => {
    const root = createRoot(element);
    root.render(<Organizations />);
});