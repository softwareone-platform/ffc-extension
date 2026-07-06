import { Card } from "@swo/design-system/card";
import { BoldText, RegularText } from "@swo/design-system/text";

import "./LegalContent.scss";

type Props = {
  appName: string;
};

export function HelpContent({ appName }: Readonly<Props>) {
  return (
    <Card className="legal-content">
      <BoldText size={4}>Help</BoldText>
      <RegularText>
        Welcome to {appName} support. Below you can find the most common ways to get assistance.
      </RegularText>

      <BoldText>Getting started</BoldText>
      <RegularText>
        Use the navigation on the left to move between sections. Each area provides an overview of
        the data and actions available to you.
      </RegularText>

      <BoldText>Contact support</BoldText>
      <RegularText>
        If you cannot find what you are looking for, reach our support team at{" "}
        <a href="mailto:support@softwareone.com">support@softwareone.com</a>. We aim to respond
        within one business day.
      </RegularText>

      <BoldText>Frequently asked questions</BoldText>
      <ul className="legal-content__list">
        <li>How do I add a new account? Use the primary action button on the relevant page.</li>
        <li>How do I export data? Use the download action in the page header.</li>
        <li>How do I change my consent? Contact support to update your preferences.</li>
      </ul>
    </Card>
  );
}
