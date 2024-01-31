import { useViewportSize } from '@mantine/hooks';
import { lazy, useEffect } from 'react';

import { setApiDefaults } from '../App';
import { Loadable } from '../functions/loading';
import { useSessionState } from '../states/SessionState';

function checkMobile() {
  const { height, width } = useViewportSize();
  if (width < 425 || height < 425) return true;
  return false;
}

const MobileAppView = Loadable(lazy(() => import('./MobileAppView')));
const DesktopAppView = Loadable(lazy(() => import('./DesktopAppView')));

// Main App
export default function MainView() {
  // Set initial login status
  useEffect(() => {
    useSessionState.getState().setLoggedIn(false);
    // Local state initialization
    setApiDefaults();
  }, []);

  // Check if mobile
  if (checkMobile()) {
    return <MobileAppView />;
  }

  // Main App component
  return <DesktopAppView />;
}
