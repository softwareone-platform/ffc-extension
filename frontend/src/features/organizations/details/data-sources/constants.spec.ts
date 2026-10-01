import type { DatasourceType } from "~api/ffc-api-model";

import { FORCE_IMPORT_ENABLED_TYPES, isForceImportEnabled } from "./constants";

describe("data-sources constants", () => {
  it.each<DatasourceType>(["aws_cnr", "azure_cnr", "gcp_cnr"])(
    "marks %s as force-import enabled",
    (type) => {
      expect(isForceImportEnabled(type)).toBe(true);
      expect(FORCE_IMPORT_ENABLED_TYPES.has(type)).toBe(true);
    },
  );

  it.each<DatasourceType>(["azure_tenant", "gcp_tenant", "unknown"])(
    "does not enable force-import for %s",
    (type) => {
      expect(isForceImportEnabled(type)).toBe(false);
    },
  );
});
