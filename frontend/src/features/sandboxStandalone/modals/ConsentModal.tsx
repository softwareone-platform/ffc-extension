import { useState } from "react";

import { Button } from "@swo/design-system/button";
import { Checkbox } from "@swo/design-system/checkbox";
import { Modal } from "@swo/design-system/modal";
import { RegularText } from "@swo/design-system/text";

const CONSENT_STORAGE_KEY = "sandboxStandalone.consent.v1";

function readStoredConsent(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return window.localStorage.getItem(CONSENT_STORAGE_KEY) === "accepted";
  } catch {
    // Sandboxed iframes can block storage access; fall back to in-memory behavior.
    return false;
  }
}

function persistConsent(): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(CONSENT_STORAGE_KEY, "accepted");
  } catch {
    // Ignore storage failures in restricted environments.
  }
}

function hasStoredConsent() {
  return readStoredConsent();
}

type Props = {
  appName: string;
};

export function ConsentModal({ appName }: Readonly<Props>) {
  const [hasConsented, setHasConsented] = useState(hasStoredConsent);
  const [isOpen, setIsOpen] = useState(() => !hasStoredConsent());

  const handleAccept = () => {
    persistConsent();
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
          To use {appName} we need your consent to process your personal data in accordance with the
          General Data Protection Regulation (GDPR / RODO).
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
