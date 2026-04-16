import React from 'react';
import { createRoot } from 'react-dom/client';
import { setup } from '@mpt-extension/sdk';
import Entitlements from './modules/Entitlements/index';

setup((element: Element) => {
    const root = createRoot(element);
    root.render(<Entitlements />);
});