import { Organizations } from "./Organizations";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { ExtensionsProvider } from "../../shared/ExtensionProvider";
import { i18n } from "../../i18n/translations";
import "./../../styles.scss";

export default () => {
  return (
    <ExtensionsProvider i18n={i18n}>
      <BrowserRouter>
        <Routes>
          <Route path={`/`} element={<Organizations />} />
        </Routes>
      </BrowserRouter>
    </ExtensionsProvider>
  );
};
