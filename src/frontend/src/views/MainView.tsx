import { MantineProvider } from '@mantine/core';
import '@mantine/core/styles.css';
import { useViewportSize } from '@mantine/hooks';
import { lazy, useEffect } from 'react';

import { setApiDefaults } from '../App';
import { Loadable } from '../functions/loading';
import { useLocalState } from '../states/LocalState';
import { theme } from '../theme';

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
    // Local state initialization
    setApiDefaults();
  }, []);

  // Check if mobile
  if (!allowMobile && checkMobile()) {
    return (
      <MantineProvider theme={theme}>
        <MobileAppView />
      </MantineProvider>
    );
  }

  // Main App component
  return (
    <MantineProvider theme={theme}>
      <DesktopAppView />
    </MantineProvider>
  );
}
