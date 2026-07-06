import { Card } from "@swo/design-system/card";
import { BoldText, RegularText } from "@swo/design-system/text";

import "./LegalContent.scss";

type Props = {
  appName: string;
};

export function TermsContent({ appName }: Readonly<Props>) {
  return (
    <Card className="legal-content">
      <BoldText size={4}>Terms and Conditions</BoldText>
      <RegularText>
        These terms and conditions govern your use of {appName}. By accessing the service you agree
        to be bound by them.
      </RegularText>

      <BoldText>1. Use of the service</BoldText>
      <RegularText>
        You agree to use {appName} only for lawful purposes and in accordance with these terms and
        any applicable agreements with SoftwareOne.
      </RegularText>

      <BoldText>2. Data protection</BoldText>
      <RegularText>
        Personal data is processed in accordance with the General Data Protection Regulation (GDPR /
        RODO). See your consent settings for details on how your data is handled.
      </RegularText>

      <BoldText>3. Availability</BoldText>
      <RegularText>
        The service is provided on an &ldquo;as is&rdquo; basis. We do not guarantee uninterrupted
        or error-free operation.
      </RegularText>

      <BoldText>4. Changes</BoldText>
      <RegularText>
        We may update these terms from time to time. Continued use of the service after changes
        constitutes acceptance of the revised terms.
      </RegularText>
    </Card>
  );
}
