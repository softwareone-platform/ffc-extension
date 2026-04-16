import OrganizationsGrid from './Grid/Organizations.Grid';
import { ExtensionsProvider } from '../../shared/ExtensionProvider';
import { i18n } from '../../i18n/translations';
import './../../styles.scss';

export default () => {
  return (
    <ExtensionsProvider i18n={i18n}>
      <OrganizationsGrid />
    </ExtensionsProvider>
  );
};
