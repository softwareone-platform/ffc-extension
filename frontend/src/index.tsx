import React from 'react';
import { createRoot } from 'react-dom/client';
import { setup } from '@mpt-extension/sdk';
import App from './App';

setup((element: Element) => {
    const root = createRoot(element);
    root.render(<App />);
});