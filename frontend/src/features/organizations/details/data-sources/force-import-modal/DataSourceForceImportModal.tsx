import { useEffect } from "react";

import { Checkbox } from "@swo/design-system/checkbox";
import { DatePicker } from "@swo/design-system/date-picker";
import { InPageHighlight } from "@swo/design-system/in-page-highlight";
import { InlineNotification } from "@swo/design-system/notification";
import { BoldText } from "@swo/design-system/text";
import { DisplayValue } from "@swo/design-system/utils";

import { DatasourceRead } from "~api/ffc-api-model";
import { Modal } from "~shared/components/modal/Modal";
import { ModalCloseResult } from "~shared/components/modal/types";
import { useFixedT } from "~shared/hooks/useFixedT";

import { useForceImportController } from "../hooks/useForceImportController";

import "./DataSourceForceImportModal.scss";

type Props = {
  isOpen: boolean;
  onClose: (result?: ModalCloseResult) => void;
  className?: string;
  datasource: DatasourceRead | null;
  organizationId: string;
};

export function DataSourceForceImportModal({
  isOpen,
  onClose,
  className,
  datasource,
  organizationId,
}: Readonly<Props>) {
  const tForceImport = useFixedT("organization:dataSources:force_import");
  const tProperties = useFixedT("organization:dataSources:force_import:properties");
  const {
    cancel,
    forceImport,
    isPending,
    error,
    reset,
    lastImportAt,
    setLastImportAt,
    isLastImportAtEnabled,
    setIsLastImportAtEnabled,
  } = useForceImportController({ onClose });

  // The modal stays mounted between openings, so clear the previous input and error each time.
  useEffect(() => {
    if (isOpen) {
      reset();
    }
  }, [isOpen, reset]);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={tForceImport("title")}
      className={className}
      testId="force-import-modal"
      onCancel={cancel}
      onSubmit={() => datasource && forceImport({ organizationId, datasource })}
      submitLabel={tForceImport("submit")}
      isSubmitting={isPending}
    >
      {error && (
        <div className="modal__error">
          <InlineNotification status="error">
            {error
              .toString()
              .split("\n")
              .map((err, i) => (
                <p key={"error_" + i}>{err}</p>
              ))}
          </InlineNotification>
        </div>
      )}
      <p>{tForceImport("confirm_line1")}</p>
      <InPageHighlight
        className="modal__properties"
        style="inline"
        direction="vertical"
        mode="dense"
      >
        <InPageHighlight.Item title={tProperties("id")}>
          <BoldText as="span" color="grey-5">
            <DisplayValue value={datasource?.datasource_id} />
          </BoldText>
        </InPageHighlight.Item>
        <InPageHighlight.Item title={tProperties("name")}>
          <BoldText as="span" color="grey-5">
            <DisplayValue value={datasource?.name} />
          </BoldText>
        </InPageHighlight.Item>
        <InPageHighlight.Item title={tProperties("linked_datasource_id")}>
          <BoldText as="span" color="grey-5">
            <DisplayValue value={datasource?.id} />
          </BoldText>
        </InPageHighlight.Item>
      </InPageHighlight>
      <p>{tForceImport("confirm_line2")}</p>
      <p>{tForceImport("confirm_line3")}</p>
      <div className="modal__field">
        <Checkbox
          className="modal__checkbox"
          label={tForceImport("use_last_import_at")}
          isChecked={isLastImportAtEnabled}
          isDisabled={isPending}
          onChange={(event) => setIsLastImportAtEnabled(event.target.checked)}
          testId="force-import-use-last-import-at"
        />
        <DatePicker<Date>
          label={tForceImport("last_import_at")}
          description={tForceImport("last_import_at_description")}
          value={lastImportAt}
          onChange={setLastImportAt}
          maxDate={new Date()}
          isDisabled={!isLastImportAtEnabled || isPending}
          testId="force-import-last-import-at"
        />
      </div>
    </Modal>
  );
}
