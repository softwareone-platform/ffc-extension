import { Outlet, useNavigate } from 'react-router-dom';

import { Button } from '@swo/design-system/button';
import { Navigation } from '@swo/design-system/navigation';

import { useMPTModal } from '@mpt-extension/sdk-react';

import { CreateUserModal } from '~features/sandboxStanalone/modals/CreateUserModal';
import { sideNavGroups } from '~features/sandboxStanalone/navigation';
import { PATHS } from '~features/sandboxStanalone/paths';
import { ConsentModal } from '~features/sandboxStanalone/modals/ConsentModal';
import { useModalToggle } from '~shared/hooks/useModalToggle';

import './StandaloneLayout.scss';

export function StandaloneLayout() {
  const navigate = useNavigate();
  const createUser = useModalToggle();
  const { open } = useMPTModal();

  return (
    <>
      <ConsentModal appName="the Sandbox Standalone" />
      <Navigation>
        <Navigation.SideNav level={2} groups={sideNavGroups} />
        <Navigation.HeaderBar title="Sandbox Standalone" subtitle="Version: 0.0.1">
          <Navigation.HeaderBar.Actions>
            <Button type="primary" onClick={() => createUser.open()}>
              Create user
            </Button>
            <span className="sandbox-standalone__header-action-label">* inside app modal</span>

            <Button
              onClick={() => open('finops.admin.create-entitlement-modal', {
                context: {}, onClose: () => {
                },
              })}
            >
              Create entitlement
            </Button>
            <span className="sandbox-standalone__header-action-label">* external entry modal</span>

            <div className="sandbox-standalone__header-actions-spacer" aria-hidden="true" />

            <Button type="primary" onClick={() => navigate(PATHS.help)}>
              Help
            </Button>
            <Button type="secondary" onClick={() => navigate(PATHS.termsAndConditions)}>
              Terms & Conditions
            </Button>
          </Navigation.HeaderBar.Actions>
        </Navigation.HeaderBar>
        <Navigation.Content>
          <Outlet />
        </Navigation.Content>
      </Navigation>

      <CreateUserModal isOpen={createUser.isOpen} onClose={createUser.close} />
    </>
  );
}
