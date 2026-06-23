import { z } from "zod/v4";

import { i18n } from "~i18n/translations";

const tValidation = i18n.getFixedT(null, null, "entitlements:addWizard:validations");

export const AddWizardFormSchema = z.object({
  id: z.string().nullish(),
  name: z.string({ error: () => tValidation("name:required") }),
  affiliate: z.object(
    {
      id: z.string({ error: () => tValidation("affiliate:required") }),
      name: z.string(),
    },
    { error: () => tValidation("affiliate:required") },
  ),
  dataSource: z.object({
    id: z.string({ error: () => tValidation("dataSource:id:required") }),
    affiliate_external_id: z.string().nullish(),
  }),
});

export type AddWizardForm = z.output<typeof AddWizardFormSchema>;
