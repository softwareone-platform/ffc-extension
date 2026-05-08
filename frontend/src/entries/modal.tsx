import { createRoot } from 'react-dom/client';
import { setup } from '@mpt-extension/sdk';
import Modal from '~features/modal/modal-widget';
import '~styles/global.scss';

setup((element: Element) => {
    const root = createRoot(element);
    root.render(<Modal />);
});
