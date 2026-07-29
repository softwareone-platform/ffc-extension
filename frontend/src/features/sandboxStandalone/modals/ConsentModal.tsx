import { useState } from "react";

import { Button } from "@swo/design-system/button";
import { Checkbox } from "@swo/design-system/checkbox";
import { Modal } from "@swo/design-system/modal";
import { RegularText } from "@swo/design-system/text";

const CONSENT_STORAGE_KEY = "sandboxStandalone.consent.v1";

function hasStoredConsent() {
  if (typeof window === "undefined") return false;
  return window.localStorage.getItem(CONSENT_STORAGE_KEY) === "accepted";
}

type Props = {
  appName: string;
};

export function ConsentModal({ appName }: Readonly<Props>) {
  const [hasConsented, setHasConsented] = useState(hasStoredConsent);
  const [isOpen, setIsOpen] = useState(() => !hasStoredConsent());

  const handleAccept = () => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(CONSENT_STORAGE_KEY, "accepted");
    }
    setIsOpen(false);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={() => undefined}
      title="Personal data processing consent (RODO)"
      closeOnEsc={false}
      isToCloseOnClickOutside={false}
      isToShowCloseButton={false}
      actions={
        <Button type="primary" isDisabled={!hasConsented} onClick={handleAccept}>
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
    </Modal>
  );
}
