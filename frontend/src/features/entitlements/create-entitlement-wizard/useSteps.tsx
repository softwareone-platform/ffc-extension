import { useMemo } from "react";

import { noop } from "@swo/design-system/utils";
import { StepProps } from "@swo/design-system/wizard";

// import { noop } from '@/Modules/Shared/FunctionUtils';
import { useFixedT } from "~shared/hooks/useFixedT";

export function useSteps(isSaving: boolean): StepProps[] {
  const tSteps = useFixedT("entitlements:addWizard:steps");
  const tActions = useFixedT("shared:actions");
  return useMemo(
    () =>
      (
        [
          {
            title: tSteps("affiliate:title"),
          },
          {
            title: tSteps("dataSource:title"),
          },
          {
            title: tSteps("overview:title"),
            nextButton: {
              label: tActions("add"),
              htmlType: "submit",
              // disable on click behaviour in favour of form onSubmit
              onClick: noop,
            },
          },
          {
            title: tSteps("summary:title"),
            nextButton: {
              isHidden: true,
            },
          },
        ] as StepProps[]
      ).map((s) => ({
        ...s,
        closeButton: {
          ...s.closeButton,
          isDisabled: isSaving,
          isHidden: s.closeButton?.isHidden ?? false,
        },
        backButton: {
          ...s.backButton,
          isDisabled: isSaving,
        },
        nextButton: {
          ...s.nextButton,
          isDisabled: isSaving,
          isBusy: isSaving,
        },
      })),
    [isSaving, tSteps, tActions],
  );
}
