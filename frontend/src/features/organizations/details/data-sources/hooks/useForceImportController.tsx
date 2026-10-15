import { useCallback, useState } from "react";

import { DatasourceRead } from "~api/ffc-api-model";
import { useOrganizationsApi } from "~organizations/api";
import { ModalControllerProps } from "~shared/components/modal/types";
import { useBaseModalController } from "~shared/hooks/useBaseModalController";
import { toIsoDateString } from "~shared/utils/DateUtils";

export function useForceImportController({ onClose }: ModalControllerProps = {}) {
  const [lastImportAt, setLastImportAt] = useState<Date | undefined>(undefined);
  const { forceReimportDatasource } = useOrganizationsApi();

  const resetLastImportAt = useCallback((): void => {
    setLastImportAt(undefined);
  }, []);

  const { error, setError, isPending, mutate, cancel } = useBaseModalController({
    namespace: "organization:dataSources:errors",
    mutationFn: ({
      organizationId,
      datasourceId,
      lastImportAt,
    }: {
      organizationId: string;
      datasourceId: string;
      lastImportAt?: Date;
    }) =>
      forceReimportDatasource(
        organizationId,
        datasourceId,
        // Omitting the body lets the backend default the import timestamps to the epoch.
        lastImportAt ? { last_import_at: toIsoDateString(lastImportAt) } : undefined,
      ),
    onClose,
    reset: resetLastImportAt,
  });

  const reset = useCallback((): void => {
    setError(null);
    resetLastImportAt();
  }, [setError, resetLastImportAt]);

  const forceImport = useCallback(
    ({
      organizationId,
      datasource,
    }: {
      organizationId: string;
      datasource: DatasourceRead;
    }): void => {
      setError(null);
      mutate({
        organizationId,
        datasourceId: datasource.id,
        lastImportAt,
      });
    },
    [mutate, lastImportAt, setError],
  );

  return {
    forceImport,
    error,
    isPending,
    cancel,
    reset,
    lastImportAt,
    setLastImportAt,
  };
}
