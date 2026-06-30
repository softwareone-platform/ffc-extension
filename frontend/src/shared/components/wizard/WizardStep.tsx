import { PropsWithChildren, useEffect, useRef } from "react";

import { InlineNotification } from "@swo/design-system/notification";
import { RegularText } from "@swo/design-system/text";

export interface WizardStepProps extends PropsWithChildren {
  readonly title: string;
  readonly error?: string;
  readonly className?: string;
  readonly contentClassName?: string;
}

export function WizardStep({
  title,
  error,
  children,
  className,
  contentClassName,
}: WizardStepProps) {
  const errorRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (error?.length && typeof errorRef?.current?.scrollIntoView === "function") {
      errorRef.current.scrollIntoView();
    }
  }, [error]);

  const contentClass = "step__content " + (contentClassName ?? "");
  return (
    <div className={`step ${className}`}>
      {error ? (
        <div ref={errorRef} className={"step__error"}>
          <InlineNotification status="error">
            {error
              .toString()
              .split("\n")
              .map((err, i) => (
                <p key={"error_" + i}>{err}</p>
              ))}
          </InlineNotification>
        </div>
      ) : (
        <></>
      )}
      <RegularText as="h4" size={4}>
        {title}
      </RegularText>
      <div className={contentClass}>{children}</div>
    </div>
  );
}
