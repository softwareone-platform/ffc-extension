import { $ZodRawIssue } from "zod/v4/core";

import type { i18n } from "./translations";

function isRecord(value: unknown): value is Record<string, unknown> {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  for (const key in value) {
    if (!Object.prototype.hasOwnProperty.call(value, key)) {
      return false;
    }
  }

  return true;
}

function getKeyAndValues(
  param: unknown,
  defaultKey: string,
): {
  values: Record<string, unknown>;
  key: string;
} {
  if (typeof param === "string") {
    return { key: param, values: {} };
  }

  if (isRecord(param)) {
    const key = "key" in param && typeof param.key === "string" ? param.key : defaultKey;
    const values = "values" in param && isRecord(param.values) ? param.values : {};
    return { key, values };
  }

  return { key: defaultKey, values: {} };
}

export function getZodMap(t: typeof i18n.t) {
  return (issue: $ZodRawIssue) => {
    const tWithDefault = ((key: string, options?: Record<string, unknown>) => {
      return t(key, { defaultValue: key, ...options });
    }) as typeof t;
    let message: string;

    message = issue.message ? t(issue.message, { defaultValue: issue.message }) : "Invalid value";

    switch (issue.code) {
      case "invalid_type":
        {
          if (issue.expected === "undefined" || issue.expected === "null") {
            message = tWithDefault("errors:invalid_type_received_" + issue.expected);
          } else {
            message = tWithDefault("errors:invalid_type", {
              expected: t(`types:${issue.expected}`, {
                defaultValue: issue.expected,
              }),
              received: t(`types:${issue.received}`, {
                defaultValue: issue.received,
              }),
            });
          }
        }
        break;
      case "invalid_value":
        {
          message = tWithDefault("errors:invalid_literal", {
            expected: JSON.stringify(issue.expected),
          });
        }
        break;
      case "unrecognized_keys":
        {
          message = tWithDefault("errors:unrecognized_keys", {
            keys: issue.keys.join(", "),
            count: issue.keys.length,
          });
        }
        break;
      case "invalid_union":
        {
          message = tWithDefault("errors:invalid_union", {});
        }
        break;
      case "invalid_format":
        {
          if (issue.format === "date") {
            message = tWithDefault("errors:invalid_date");
          } else if (issue.format === "starts_with") {
            message = tWithDefault(`errors.invalid_string.startsWith`, {
              startsWith: issue.format,
            });
          } else if (issue.format === "ends_with") {
            message = tWithDefault(`errors.invalid_string.endsWith`, {
              endsWith: issue.format,
            });
          } else {
            message = tWithDefault(`errors.invalid_string.${issue.format}`, {
              validation: t(`validations.${issue.format}`, {
                defaultValue: issue.format,
              }),
            });
          }
        }
        break;
      case "too_small": {
        const minimum = issue.origin === "date" ? new Date(Number(issue.minimum)) : issue.minimum;
        message = tWithDefault(
          `errors.too_small.${issue.origin}.${issue.exact ? "exact" : issue.inclusive ? "inclusive" : "not_inclusive"}`,
          {
            minimum,
            count: typeof minimum === "number" ? minimum : undefined,
          },
        );
        break;
      }
      case "too_big": {
        const maximum = issue.origin === "date" ? new Date(Number(issue.maximum)) : issue.maximum;
        message = tWithDefault(
          `errors.too_big.${issue.origin}.${issue.exact ? "exact" : issue.inclusive ? "inclusive" : "not_inclusive"}`,
          {
            maximum,
            count: typeof maximum === "number" ? maximum : undefined,
          },
        );
        break;
      }
      case "custom": {
        const { key, values } = getKeyAndValues(issue.params?.i18n, "errors:custom");

        message = t(key, {
          ...values,
        });
        break;
      }
      case "not_multiple_of":
        {
          message = tWithDefault("errors:not_multiple_of", {
            multipleOf: issue.divisor,
          });
        }
        break;
      default:
    }

    return { message };
  };
}
