import { useCallback, useState } from "react";

import { zodResolver } from "@hookform/resolvers/zod/dist/zod.js";
import { useMutation } from "@tanstack/react-query";
import { FormProvider, useForm } from "react-hook-form";

import { Wizard, WizardContextProps } from "@swo/design-system/wizard";

import { useMPTModal } from "@mpt-extension/sdk-react";

import { AddWizardForm, AddWizardFormSchema } from "./CreateEntitlement.Schema";
import { AffiliateStep } from "./steps/AffiliateStep";
import { DataSourceStep } from "./steps/DataSourceStep";
import { ReviewStep } from "./steps/ReviewStep";
import { SummaryStep } from "./steps/SummaryStep";
import { useSteps } from "./useSteps";

import "./CreateEntitlement.scss";

import { useEntitlementsApi } from "~entitlements/api/useEntitlementsApi";
import { useFixedT } from "~shared/hooks/useFixedT";

export default () => {
  const tEntitlementWizard = useFixedT("entitlements:addWizard");
  const [activeStepIndex, setActiveStepIndex] = useState(0);
  const [entitlementCreated, setEntitlementCreated] = useState(false);
  const [error, setError] = useState("");
  const { save } = useEntitlementsApi();
  const { mutateAsync, isPending } = useMutation({
    mutationFn: save,
  });
  const { close } = useMPTModal();
  const steps = useSteps(isPending);

  const methods = useForm({
    resolver: zodResolver(AddWizardFormSchema),
    mode: "onChange",
  });
  const { handleSubmit, reset, setValue } = methods;

  const onSave = useCallback(() => {
    alert("saved");
  }, []);

  // const onError = useCallback((err: Error): void => setError(err.message), []);

  const onClose = useCallback(() => {
    const closeContext = { entitlementCreated };
    close(closeContext);
  }, [entitlementCreated, close]);

  const closeWizard = useCallback(() => {
    reset();
    setError("");
    onClose?.();
  }, [onClose, reset]);

  const onSubmit = useCallback(
    async (form: AddWizardForm) => {
      try {
        const res = await mutateAsync({
          name: form.name,
          affiliate_external_id: form.dataSource.affiliate_external_id || "",
          datasource_id: form.dataSource.id,
          owner: {
            id: form.affiliate.id,
          },
        });

        setValue("id", res.data?.id);

        if (res.status !== 201) {
          setError(res.statusText);
          return;
        }

        setEntitlementCreated(true);

        setActiveStepIndex((i) => i + 1);
        // wizardRef.current?.goToNext();
      } catch (err) {
        setError(err + "");
      }
    },
    [mutateAsync, setValue],
  );

  return (
    <div className="wizard">
      <FormProvider {...methods}>
        <Wizard
          testId={"create-entitlement-wizard"}
          stepsProps={steps}
          onClose={closeWizard}
          onSave={onSave}
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
                    return <SummaryStep />;
                }
              }}
            </Wizard.Content.StepContent>
          </Wizard.Content>
          <Wizard.Actions />
        </Wizard>
      </FormProvider>
    </div>
  );
};
