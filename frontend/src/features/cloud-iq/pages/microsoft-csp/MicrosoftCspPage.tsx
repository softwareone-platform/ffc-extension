import { useState } from "react";

import { Button } from "@swo/design-system/button";
import { Card } from "@swo/design-system/card";
import { Grid } from "@swo/design-system/grid";
import { Icon } from "@swo/design-system/icon";
import { Select } from "@swo/design-system/select";
import { BoldText } from "@swo/design-system/text";

import { useGridConfig } from "./MicrosoftAccountsGrid.config";
import { MicrosoftAccount, accountFilterOptions } from "./microsoft-accounts.mock";

import "./MicrosoftCspPage.scss";

export function MicrosoftCspPage() {
  const gridProps = useGridConfig();
  const [accountFilter, setAccountFilter] = useState(accountFilterOptions[0].value);

  return (
    <div className="cloud-iq-microsoft-csp">
      <header className="cloud-iq-microsoft-csp__header">
        <BoldText size={4}>Microsoft Accounts</BoldText>
        <div className="cloud-iq-microsoft-csp__actions">
          <Button type="primary" icon={<Icon name="add" size={18} />}>
            Add Account
          </Button>
          <Button type="secondary" icon={<Icon name="download" size={18} />}>
            {""}
          </Button>
          <Button type="secondary" icon={<Icon name="copy_content" size={18} />}>
            {""}
          </Button>
        </div>
      </header>

      <Card className="cloud-iq-microsoft-csp__card">
        <div className="cloud-iq-microsoft-csp__toolbar">
          <Select
            className="cloud-iq-microsoft-csp__filter"
            options={accountFilterOptions}
            value={accountFilter}
            onChange={setAccountFilter}
          />
        </div>
        <Grid<MicrosoftAccount> {...gridProps} />
      </Card>
    </div>
  );
}
