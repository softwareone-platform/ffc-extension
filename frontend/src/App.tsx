import {useMemo, useCallback, Suspense} from 'react';
import {BrowserRouter, Route, Routes} from 'react-router-dom';
import {Navigation} from '@swo/design-system/navigation';
import './styles.scss';
import Entitlements from "./modules/Entitlements";
import {Button} from "@swo/design-system/button";

export default () => {
    return (
        <Entitlements/>
    )
};