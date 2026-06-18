import { Navigate, Route } from "react-router-dom";

import { mountFeatureEntry } from "~app/bootstrap/MountFeatureEntry";
import { DetailsLayout } from "~app/layouts";
import { EntitlementDetailsHeader } from "~features/entitlements/components/EntitlementDetailsHeader";
import { EntitlementDetailsContent } from "~features/entitlements/details/DetailsContent";
import { EntitlementsGeneralDetails } from "~features/entitlements/details/general/General";
import { EntitlementsGrid } from "~features/entitlements/list/EntitlementsGrid";
import { PARAMS, SEGMENTS } from "~features/entitlements/paths";

mountFeatureEntry(
  <>
    <Route index element={<EntitlementsGrid />} />
    <Route
      path={SEGMENTS.idParam}
      element={
        <DetailsLayout
          paramKey={PARAMS.entitlementId}
          renderHeader={(id, backUrl) => (
            <EntitlementDetailsHeader entitlementId={id} backUrl={backUrl} />
          )}
        >
          <EntitlementDetailsContent />
        </DetailsLayout>
      }
    >
      <Route index element={<Navigate to={SEGMENTS.general} replace />} />
      <Route path={SEGMENTS.general} element={<EntitlementsGeneralDetails />} />
    </Route>
  </>,
);
