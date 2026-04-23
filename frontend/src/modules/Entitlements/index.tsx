import EntitlementsGrid from './Grid/Entitlements.Grid';
import { ExtensionsProvider } from '../../shared/providers/ExtensionProvider';
import { i18n } from '../../i18n/translations';
import './../../styles.scss';

export default () => {
  return (
    <ExtensionsProvider i18n={i18n}>
      <EntitlementsGrid />
    </ExtensionsProvider>
  );
};
