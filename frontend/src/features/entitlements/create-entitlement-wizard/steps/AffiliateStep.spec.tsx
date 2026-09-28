import type { ComponentProps } from "react";

import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { StepNavigationProperties } from "@swo/design-system/wizard";

import type { SelectAffiliateList } from "~shared/components/SelectAffiliateList";
import { makeAccount } from "~test-utils";
import { mockSharedWizardStep } from "~test-utils/mocks/wizardStep";

import { AffiliateStep } from "./AffiliateStep";
import { renderWizardStep } from "./wizardStepTestUtils";

const mockRegisterOnNextCallback = jest.fn();
type MockSelectAffiliateListProps = ComponentProps<typeof SelectAffiliateList>;
const selectedAffiliate = makeAccount({ id: "acc-1" });

const mockSelectAffiliateList = jest.fn() as jest.MockedFunction<
  (props: MockSelectAffiliateListProps) => void
>;

jest.mock("@swo/design-system/wizard", () => ({
  useStepActions: () => ({ registerOnNextCallback: mockRegisterOnNextCallback }),
}));

jest.mock("~shared/components/SelectAffiliateList", () => ({
  SelectAffiliateList: (props: MockSelectAffiliateListProps) => {
    mockSelectAffiliateList(props);
    return (
      <button onClick={() => props.onSelected(selectedAffiliate)} type="button">
        select affiliate
      </button>
    );
  },
}));

jest.mock("~shared/components/wizard/WizardStep", () => mockSharedWizardStep);

function renderStep(triggerResolvedValue = true) {
  return renderWizardStep(<AffiliateStep />, { triggerResolvedValue });
}

function getRegisteredOnNextCallback() {
  return mockRegisterOnNextCallback.mock.lastCall![0] as (
    props: StepNavigationProperties,
  ) => Promise<number>;
}

describe("AffiliateStep", () => {
  it("renders SelectAffiliateList wired to setValue via onSelected", async () => {
    const user = userEvent.setup();
    const { setValue } = renderStep();

    await user.click(screen.getByRole("button", { name: "select affiliate" }));

    expect(setValue).toHaveBeenCalledWith("affiliate", selectedAffiliate, { shouldValidate: true });
  });

  it("validates the affiliate selection before advancing", async () => {
    const { trigger } = renderStep();

    const onNext = getRegisteredOnNextCallback();
    const nextIndex = await onNext({
      targetStepIndex: 1,
      currentStepIndex: 0,
    } as StepNavigationProperties);

    expect(trigger).toHaveBeenCalledWith("affiliate", { shouldFocus: false });
    expect(nextIndex).toBe(1);
  });

  it("stays on the current step when validation fails", async () => {
    renderStep(false);

    const onNext = getRegisteredOnNextCallback();
    const nextIndex = await onNext({
      targetStepIndex: 1,
      currentStepIndex: 0,
    } as StepNavigationProperties);

    expect(nextIndex).toBe(0);
  });
});
