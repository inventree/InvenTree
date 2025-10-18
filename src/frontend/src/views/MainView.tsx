import '@mantine/core/styles.css';
import { useViewportSize } from '@mantine/hooks';
import { lazy, useEffect } from 'react';
import { useShallow } from 'zustand/react/shallow';

import { setApiDefaults } from '../App';
import { Loadable } from '../functions/loading';
import { useLocalState } from '../states/LocalState';

function checkMobile() {
  const { height, width } = useViewportSize();
  if (width < 425 || height < 425) return true;
  return false;
}

const MobileAppView = Loadable(
  lazy(() => import('./MobileAppView')),
  true,
  true
);
const DesktopAppView = Loadable(
  lazy(() => import('./DesktopAppView')),
  true,
  true
);

// Main App
export default function MainView() {
  const [allowMobile] = useLocalState(
    useShallow((state) => [state.allowMobile])
  );
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
  if (
    !allowMobile &&
    window.INVENTREE_SETTINGS.mobile_mode !== 'allow-always' &&
    checkMobile()
  ) {
    return <MobileAppView />;
  }

  // Main App component
  return <DesktopAppView />;
}
