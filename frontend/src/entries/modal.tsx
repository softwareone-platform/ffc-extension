import { createRoot } from 'react-dom/client';

import Modal from '~features/modal/ModalWidget';

import '~styles/global.scss';

import { setup } from '@mpt-extension/sdk';

setup((element: Element) => {
    const root = createRoot(element);
    root.render(<Modal />);
});
