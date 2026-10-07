import { PropsWithChildren } from "react";

import { MediumText } from "@swo/design-system/text";

import style from "./CardSection.module.scss";

export interface CardSectionProps extends PropsWithChildren {
  title: string;
}

export function CardSection({ children, title }: CardSectionProps) {
  return (
    <div className={style["card-section"]}>
      <div className={style["card-section-title"]}>
        <MediumText size={4}>{title}</MediumText>
      </div>
      <div className={style["card-section-content"]}>{children}</div>
    </div>
  );
}
