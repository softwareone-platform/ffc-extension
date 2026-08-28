import { ReactNode } from "react";

import { Card } from "@swo/design-system/card";

export type PanelProps = {
  title: string;
  children: ReactNode;
  className?: string;
};

export function Panel({ title, children, className }: PanelProps) {
  return (
    <Card className={`ffc-panel ${className ?? ""}`}>
      <h3 className={"ffc-panel__title"}>{title}</h3>
      {children}
    </Card>
  );
}
