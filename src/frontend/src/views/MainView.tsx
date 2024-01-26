import { useViewportSize } from '@mantine/hooks';
import { lazy } from 'react';

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
  // Check if mobile
  if (checkMobile()) {
    return <MobileAppView />;
  }

  // Main App component
  return <DesktopAppView />;
}
