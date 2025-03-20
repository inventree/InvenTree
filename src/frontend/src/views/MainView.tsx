import '@mantine/core/styles.css';
import { useViewportSize } from '@mantine/hooks';
import { lazy, useEffect } from 'react';

import { setApiDefaults } from '@lib/functions/api';
import { useLocalState } from '../../lib/states/LocalState';
import { Loadable } from '../functions/loading';

function checkMobile() {
  const { height, width } = useViewportSize();
  if (width < 425 || height < 425) return true;
  return false;
}

const MobileAppView = Loadable(lazy(() => import('./MobileAppView')));
const DesktopAppView = Loadable(lazy(() => import('./DesktopAppView')));

// Main App
export default function MainView() {
  const [allowMobile] = useLocalState((state) => [state.allowMobile]);
  // Set initial login status
  useEffect(() => {
    try {
      // Local state initialization
      setApiDefaults();
    } catch (e) {
      console.error(e);
    }
  }, []);

  // Check if mobile
  if (!allowMobile && checkMobile()) {
    return <MobileAppView />;
  }

  // Main App component
  return <DesktopAppView />;
}
