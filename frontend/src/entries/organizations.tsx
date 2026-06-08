import { Route } from "react-router-dom";

import { DetailsLayout } from "~app/layouts";
import { mountFeatureEntry } from "~app/bootstrap/MountFeatureEntry";
import { OrganizationDetailsHeader } from "~features/organizations/components/OrganizationDetailsHeader";
import { OrganizationDataSources } from "~features/organizations/details/data-sources/DataSources";
import { OrganizationDetailsContent } from "~features/organizations/details/DetailsContent";
import { OrganizationGeneralDetails } from "~features/organizations/details/general/General";
import { OrganizationUsers } from "~features/organizations/details/users/Users";
import { OrganizationsGrid } from "~features/organizations/list/OrganizationsGrid";
import { PARAMS, SEGMENTS } from "~features/organizations/paths";

mountFeatureEntry(
  <>
    <Route index element={<OrganizationsGrid />} />
    <Route
      path={SEGMENTS.idParam}
      element={
        <DetailsLayout
          paramKey={PARAMS.organizationId}
          renderHeader={(id, backUrl) => (
            <OrganizationDetailsHeader organizationId={id} backUrl={backUrl} />
          )}
        >
          <OrganizationDetailsContent />
        </DetailsLayout>
      }
    >
      <Route index element={<OrganizationGeneralDetails />} />
      <Route path={SEGMENTS.general} element={<OrganizationGeneralDetails />} />
      <Route path={SEGMENTS.dataSources} element={<OrganizationDataSources />} />
      <Route path={SEGMENTS.users} element={<OrganizationUsers />} />
    </Route>
  </>,
);
