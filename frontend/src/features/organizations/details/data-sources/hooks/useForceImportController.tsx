import { useCallback, useState } from "react";

import { useMutation } from "@tanstack/react-query";
import { AxiosError } from "axios";

import { DatasourceRead } from "~api/ffc-api-model";
import { useOrganizationsApi } from "~organizations/api";
import { ModalControllerProps } from "~shared/components/modal/types";
import { useFixedT } from "~shared/hooks/useFixedT";
import { toIsoDateString } from "~shared/utils/DateUtils";

export function useForceImportController({ onClose }: ModalControllerProps = {}) {
  const [error, setError] = useState<string | null>(null);
  const [lastImportAt, setLastImportAt] = useState<Date | undefined>(undefined);
  const [isLastImportAtEnabled, setIsLastImportAtEnabled] = useState(false);
  const { forceReimportDatasource } = useOrganizationsApi();
  const tErrors = useFixedT("organization:dataSources:errors");

  const reset = useCallback((): void => {
    setError(null);
    setLastImportAt(undefined);
    setIsLastImportAtEnabled(false);
  }, []);

  const cancel = useCallback((): void => {
    reset();
    if (onClose) {
      onClose();
    }
  }, [onClose, reset]);

  const onError = useCallback(
    (err: AxiosError): void => {
      const status = err.response?.status ?? err.status ?? "unknown";
      setError(tErrors("force_import_failed_with_code_" + status));
    },
    [tErrors],
  );

  const onSuccess = useCallback((): void => {
    reset();
    if (onClose) {
      onClose({ success: true });
    }
  }, [onClose, reset]);

  const { mutate, isPending } = useMutation({
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
    onSuccess,
    onError,
  });

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
        lastImportAt: isLastImportAtEnabled ? lastImportAt : undefined,
      });
    },
    [mutate, isLastImportAtEnabled, lastImportAt],
  );

  return {
    forceImport,
    error,
    isPending,
    cancel,
    reset,
    lastImportAt,
    setLastImportAt,
    isLastImportAtEnabled,
    setIsLastImportAtEnabled,
  };
}
