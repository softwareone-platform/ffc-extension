import { useState } from "react";

import { Button } from "@swo/design-system/button";
import { Checkbox } from "@swo/design-system/checkbox";
import { RegularText } from "@swo/design-system/text";

import { StandaloneModal } from "~shared/components/modal/StandaloneModal";

import "./ConsentModal.scss";

type Props = {
  appName: string;
};

export function ConsentModal({ appName }: Readonly<Props>) {
  const [isOpen, setIsOpen] = useState(true);
  const [hasConsented, setHasConsented] = useState(false);

  return (
    <StandaloneModal
      isOpen={isOpen}
      onClose={() => undefined}
      title="Personal data processing consent (RODO)"
      closeOnEsc={false}
      isToCloseOnClickOutside={false}
      isToShowCloseButton={false}
      actions={
        <Button type="primary" isDisabled={!hasConsented} onClick={() => setIsOpen(false)}>
          Accept and continue
        </Button>
      }
    >
      <div className="consent-modal">
        <RegularText>
          To use {appName} we need your consent to process your personal data in accordance with
          the General Data Protection Regulation (GDPR / RODO).
        </RegularText>
        <RegularText>
          Your data will be processed solely to provide and improve this service. You may withdraw
          your consent at any time and request access, rectification, or deletion of your data.
        </RegularText>
        <Checkbox
          isChecked={hasConsented}
          onChange={(e) => setHasConsented(e.target.checked)}
          label="I consent to the processing of my personal data in accordance with the GDPR (RODO)."
        />
      </div>
    </StandaloneModal>
  );
}
