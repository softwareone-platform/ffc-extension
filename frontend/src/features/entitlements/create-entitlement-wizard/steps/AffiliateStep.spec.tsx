import type { StepNavigationProperties } from "@swo/design-system/wizard";

import type { Account } from "~features/entitlements/api/model";
import { makeAccount } from "~test-utils";
import { mockSharedWizardStep } from "~test-utils/mocks/wizardStep";

import { renderWizardStep } from "./wizardStepTestUtils";
import { AffiliateStep } from "./AffiliateStep";

const mockRegisterOnNextCallback = jest.fn();
const mockSelectAffiliateList = jest.fn() as jest.MockedFunction<
  (props: { entity: Account; onSelected: (a: Account) => void }) => void
>;

jest.mock("@swo/design-system/wizard", () => ({
  useStepActions: () => ({ registerOnNextCallback: mockRegisterOnNextCallback }),
}));

jest.mock("~shared/components/SelectAffiliateList", () => ({
  SelectAffiliateList: (props: { entity: Account; onSelected: (a: Account) => void }) => {
    mockSelectAffiliateList(props);
    return <div data-testid="select-affiliate-list" />;
  },
}));

jest.mock("~shared/components/wizard/WizardStep", () => mockSharedWizardStep);

function renderStep(triggerResolvedValue = true) {
  return renderWizardStep(<AffiliateStep />, { triggerResolvedValue });
}

describe("AffiliateStep", () => {
  it("renders SelectAffiliateList wired to setValue via onSelected", () => {
    const { setValue } = renderStep();

    const props = mockSelectAffiliateList.mock.lastCall![0];
    const account = makeAccount({ id: "acc-1" });
    props.onSelected(account);

    expect(setValue).toHaveBeenCalledWith("affiliate", account, { shouldValidate: true });
  });

  it("registers an onNext callback that validates affiliate and advances on success", async () => {
    const { trigger } = renderStep();

    const onNext = mockRegisterOnNextCallback.mock.lastCall![0] as (
      p: StepNavigationProperties,
    ) => Promise<number>;
    const nextIndex = await onNext({
      targetStepIndex: 1,
      currentStepIndex: 0,
    } as StepNavigationProperties);

    expect(trigger).toHaveBeenCalledWith("affiliate", { shouldFocus: false });
    expect(nextIndex).toBe(1);
  });

  it("stays on the current step when validation fails", async () => {
    renderStep(false);

    const onNext = mockRegisterOnNextCallback.mock.lastCall![0] as (
      p: StepNavigationProperties,
    ) => Promise<number>;
    const nextIndex = await onNext({
      targetStepIndex: 1,
      currentStepIndex: 0,
    } as StepNavigationProperties);

    expect(nextIndex).toBe(0);
  });
});
