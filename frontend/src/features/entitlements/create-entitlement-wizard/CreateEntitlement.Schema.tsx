import { z } from "zod/v4";

import { i18n } from "~i18n/translations";

const tValidation = i18n.getFixedT(null, null, "entitlements:addWizard:validations");

/**
 * Builds a full-match RegExp from an API-provided pattern.
 * Returns `null` for a missing or malformed pattern so that validation is skipped
 * instead of crashing the form; the backend remains the source of truth.
 */
export const toDatasourceIdRegExp = (pattern: string | null | undefined): RegExp | null => {
  if (!pattern) return null;
  try {
    return new RegExp(`^(?:${pattern})$`);
  } catch {
    return null;
  }
};

export const AddWizardFormSchema = z
  .object({
    id: z.string().nullish(),
    name: z.string({ error: () => tValidation("name:required") }),
    affiliate: z.object(
      {
        id: z.string({ error: () => tValidation("affiliate:required") }),
        name: z.string(),
        integration: z.string().nullish(),
        // Declared so it survives parsing and is available to the refinement below.
        cloud_provider: z.object({ datasource_id_format: z.string() }).nullish(),
      },
      { error: () => tValidation("affiliate:required") },
    ),
    dataSource: z.object({
      id: z.string({ error: () => tValidation("dataSource:id:required") }),
      affiliate_external_id: z.string({
        error: () => tValidation("dataSource:affiliate_external_id:required"),
      }),
    }),
  })
  .superRefine(({ affiliate, dataSource }, ctx) => {
    const regex = toDatasourceIdRegExp(affiliate.cloud_provider?.datasource_id_format);

    if (regex && !regex.test(dataSource.id)) {
      ctx.addIssue({
        code: "custom",
        path: ["dataSource", "id"],
        message: tValidation("dataSource:id:invalid", {
          format: affiliate.cloud_provider?.datasource_id_format,
        }),
      });
    }
  });

export type AddWizardForm = z.output<typeof AddWizardFormSchema>;
