import { ReactNode } from "react";

import { Card } from "@swo/design-system/card";

import "./ErrorPage.module.scss";

export type Props = {
  title: ReactNode;
  subtitle?: ReactNode;
  errorDescription?: ReactNode;
  className?: string;
};

export function ErrorPage({ title, subtitle, errorDescription, className }: Props) {
  return (
    <div className={"error-page"}>
      <Card>
        <div className={`error-page-content ${className ?? ""}`}>
          <h1>{title}</h1>
          {subtitle && <h2>{subtitle}</h2>}
          {errorDescription && <p>{errorDescription}</p>}
        </div>
      </Card>
    </div>
  );
}
