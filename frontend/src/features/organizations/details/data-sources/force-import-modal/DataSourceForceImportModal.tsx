import { useEffect } from "react";

import { DatePicker } from "@swo/design-system/date-picker";
import { InPageHighlight } from "@swo/design-system/in-page-highlight";
import { InlineNotification } from "@swo/design-system/notification";
import { BoldText, RegularText } from "@swo/design-system/text";
import { DisplayValue } from "@swo/design-system/utils";

import { DatasourceRead } from "~api/ffc-api-model";
import DataSourceIcon from "~shared/components/custom-icons/CustomIcon";
import { Modal } from "~shared/components/modal/Modal";
import { ModalCloseResult } from "~shared/components/modal/types";
import { useFixedT } from "~shared/hooks/useFixedT";

import { useForceImportController } from "../hooks/useForceImportController";

import "./DataSourceForceImportModal.scss";

import { EntityReferenceCell } from "@swo/design-system/entity-reference-cell";

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

  const { cancel, forceImport, isPending, error, reset, lastImportAt, setLastImportAt } =
    useForceImportController({ onClose });

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
      <InlineNotification status="info">
        <p>{tForceImport("confirm_line3")}</p>
      </InlineNotification>
      <div className="modal__datasource_info">
        <RegularText>{tForceImport("confirm_line1")}</RegularText>
        <EntityReferenceCell
          primaryContent={datasource?.name || ""}
          secondaryContent={datasource?.datasource_id || ""}
          secondaryContentMaxHeight={50}
          icon={<DataSourceIcon name={datasource?.type || "unknown"} size={48} />}
        />
      </div>
      <div className="modal__datasource_properties">
        <InPageHighlight
          className="modal__properties"
          style="inline"
          direction="vertical"
          mode="dense"
        >
          <InPageHighlight.Item title={tProperties("linked_datasource_id")}>
            <BoldText as="span" color="grey-5">
              <DisplayValue value={datasource?.id} />
            </BoldText>
          </InPageHighlight.Item>
        </InPageHighlight>
      </div>
      <div className="modal__field">
        <DatePicker<Date>
          label={tForceImport("last_import_at")}
          description={tForceImport("last_import_at_description")}
          value={lastImportAt}
          onChange={setLastImportAt}
          maxDate={new Date()}
          placeholder={tForceImport("last_import_at_placeholder")}
          isDisabled={isPending}
          testId="force-import-last-import-at"
          popoverCssPosition="fixed"
          positions={{ position: "top-end", offset: { x: 0, y: -12 } }}
        />
      </div>

      <p>
        <i>{tForceImport("confirm_line2")}</i>
      </p>
    </Modal>
  );
}
