import React from 'react';
import { createRoot } from 'react-dom/client';
import { setup } from '@mpt-extension/sdk';
import Modal from './modules/Modal';
import './styles.scss';

setup((element: Element) => {
    const root = createRoot(element);
    root.render(<Modal />);
});