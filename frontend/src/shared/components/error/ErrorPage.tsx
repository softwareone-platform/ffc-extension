import { ReactNode, useCallback, useRef } from "react";

import { Card } from "@swo/design-system/card";
import { Icon } from "@swo/design-system/icon";

import "./ErrorPage.module.scss";

import { useNavigate } from "react-router-dom";

import { Button } from "@swo/design-system/button";

import { useFixedT } from "~shared/hooks/useFixedT";

export type Props = {
  readonly title: ReactNode;
  readonly subtitle?: ReactNode;
  readonly errorDescription?: ReactNode;
  readonly className?: string;
};

export function ErrorPage({ title, subtitle, errorDescription, className }: Props) {
  const tError = useFixedT("errorPage");
  const navigate = useNavigate();
  const errorDescriptionRef = useRef<HTMLDivElement>(null);

  const onHomeClick = useCallback((evt: React.MouseEvent<HTMLAnchorElement>) => {
    evt.preventDefault();
    navigate("/");
  }, []);

  return (
    <div className={`page page-embedded ${className}`}>
      <div className={"error-page-card__container"}>
        <Card>
          <div className={"error-page-card__content"}>
            <div className={"error-page-card__content__icon"}>
              <Icon name="release_alert" size={100} color="black" />
            </div>
            <h2 className={"error-page-card__content__title"}>{title}</h2>
            {subtitle && <p className={"error-page-card__content__subtitle"}>{subtitle}</p>}

            {errorDescription && (
              <div className={"error-page-card__content__error-description__field"}>
                <div className={"error-page-card__content__error-description__field__value"}>
                  <div
                    ref={errorDescriptionRef}
                    className={"error-page-card__content__error-description__field__value__content"}
                  >
                    {errorDescription}
                  </div>
                </div>
              </div>
            )}

            <div className={"error-page-card__content__actions"}>
              <a href="/" onClick={onHomeClick}>
                <Button type="text">{tError("error-handler:errorPageCard:home")}</Button>
              </a>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
