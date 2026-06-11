import { ReactNode } from "react";

import "./ModalWidget.scss";

type Props = {
  title: ReactNode;
  children: ReactNode;
};

export function ModalWidget({ title, children }: Props) {
  return (
    <div className="modal">
      <div className="modal-header modal__container">
        <div className="modal-header-title">{title}</div>
      </div>
      {children}
    </div>
  );
}
