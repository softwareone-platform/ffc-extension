import { ReactNode } from "react";

import "./EntryModalWidget.scss";

type Props = {
  title: ReactNode;
  children: ReactNode;
};

export function EntryModalWidget({ title, children }: Readonly<Props>) {
  return (
    <div className="modal">
      <div className="modal-header modal__container">
        <div className="modal-header-title">{title}</div>
      </div>
      {children}
    </div>
  );
}
