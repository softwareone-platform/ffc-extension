import { useCallback, useState } from "react";

import { zodResolver } from "@hookform/resolvers/zod/dist/zod.js";
import { useMutation } from "@tanstack/react-query";
import { FormProvider, useForm } from "react-hook-form";

import { Modal } from "@swo/design-system/modal";
import { Wizard, WizardContextProps } from "@swo/design-system/wizard";

import { useEntitlementsApi } from "~entitlements/api/useEntitlementsApi";
import { ModalCloseResult } from "~shared/components/modal/types";
import { useFixedT } from "~shared/hooks/useFixedT";
import { useUserRole } from "~shared/hooks/useUserRole";

import { AddWizardForm, AddWizardFormSchema } from "./CreateEntitlement.Schema";
import { AffiliateStep } from "./steps/AffiliateStep";
import { DataSourceStep } from "./steps/DataSourceStep";
import { ReviewStep } from "./steps/ReviewStep";
import { SummaryStep } from "./steps/SummaryStep";
import { useSteps } from "./useSteps";

type Props = {
  isOpen: boolean;
  onClose: (result?: ModalCloseResult) => void;
};

export function CreateEntitlementWizard({ isOpen, onClose }: Readonly<Props>) {
  const tEntitlementWizard = useFixedT("entitlements:addWizard");
  const [activeStepIndex, setActiveStepIndex] = useState(0);
  const [entitlementCreated, setEntitlementCreated] = useState(false);
  const [error, setError] = useState("");
  const { save } = useEntitlementsApi();
  const { mutateAsync, isPending } = useMutation({ mutationFn: save });
  const steps = useSteps(isPending);
  const { user, role } = useUserRole();

  const methods = useForm({
    resolver: zodResolver(AddWizardFormSchema),
    mode: "onChange",
    defaultValues: {
      affiliate:
        role === "affiliate"
          ? { id: user?.account.id || "", name: user?.account.name || "" }
          : null,
    },
  });
  const { handleSubmit, reset, setValue } = methods;

  const closeWizard = useCallback(() => {
    reset();
    setError("");
    setActiveStepIndex(0);
    onClose({ success: entitlementCreated });
  }, [reset, onClose, entitlementCreated]);

  const finish = useCallback(() => {
    onClose({ success: entitlementCreated });
    setActiveStepIndex(0);
  }, [onClose, entitlementCreated]);

  const onSubmit = useCallback(
    async (form: AddWizardForm) => {
      try {
        const basePayload = {
          name: form.name,
          affiliate_external_id: form.dataSource.affiliate_external_id || "",
          datasource_id: form.dataSource.id,
        };

        const res = await mutateAsync(
          role === "affiliate" ? basePayload : { ...basePayload, owner: { id: form.affiliate.id } },
        );

        setValue("id", res.data?.id);

        if (res.status !== 201) {
          setError(res.statusText);
          return;
        }

        setEntitlementCreated(true);
        setActiveStepIndex((i) => i + 1);
      } catch (err) {
        setError(err + "");
      }
    },
    [mutateAsync, role, setValue],
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={() => onClose()}
      isFullScreen
      isToHidePadding
      testId="create-entitlement-wizard-modal"
    >
      <FormProvider {...methods}>
        <Wizard
          testId="create-entitlement-wizard"
          stepsProps={steps}
          onClose={closeWizard}
          onSave={finish}
          isToDisableSideNavigation={true}
          onSubmit={handleSubmit(onSubmit)}
          activeStepIndex={activeStepIndex}
          onActiveStepIndexChange={setActiveStepIndex}
        >
          <Wizard.Header>{tEntitlementWizard("title")}</Wizard.Header>
          <Wizard.Content>
            <Wizard.Content.Steps />
            <Wizard.Content.StepContent>
              {({ activeStepIndex }: WizardContextProps) => {
                switch (activeStepIndex) {
                  case 0:
                    return <AffiliateStep />;
                  case 1:
                    return <DataSourceStep />;
                  case 2:
                    return <ReviewStep error={error} />;
                  case 3:
                    return <SummaryStep error={error} />;
                }
              }}
            </Wizard.Content.StepContent>
          </Wizard.Content>
          <Wizard.Actions />
        </Wizard>
      </FormProvider>
    </Modal>
  );
}
