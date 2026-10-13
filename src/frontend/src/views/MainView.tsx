import '@mantine/core/styles.css';
import { getBaseUrl } from '@lib/functions/Navigation';
import { useViewportSize } from '@mantine/hooks';
import { type ComponentType, useEffect, useState } from 'react';
import { useShallow } from 'zustand/react/shallow';

import { setApiDefaults } from '../App';
import { useLocalState } from '../states/LocalState';

// Import both views eagerly (outside React.lazy/Suspense): a lazy component
// always suspends on its first render, and React's Suspense commit-delay
// heuristic can then hold that first commit - and every effect beneath it,
// including locale and layout loading - back by several hundred ms, even
// though the underlying chunk is already cached by the time it's needed.
const desktopViewPromise = import('./DesktopAppView').then((m) => m.default);
const mobileViewPromise = import('./MobileAppView').then((m) => m.default);

// Main App
export default function MainView() {
  const [allowMobile] = useLocalState(
    useShallow((state) => [state.allowMobile])
  );
  const [DesktopView, setDesktopView] = useState<ComponentType | null>(null);
  const [MobileView, setMobileView] = useState<ComponentType | null>(null);
  const { height, width } = useViewportSize();
  const [pathname, setPathname] = useState(window.location.pathname);
  useEffect(() => {
    const update = () => setPathname(window.location.pathname);
    window.addEventListener('cangxu-route-change', update);
    window.addEventListener('popstate', update);
    return () => {
      window.removeEventListener('cangxu-route-change', update);
      window.removeEventListener('popstate', update);
    };
  }, []);

  // Set initial login status
  useEffect(() => {
    try {
      // Local state initialization
      setApiDefaults();
    } catch (e) {
      console.error(e);
    }
  }, []);

  useEffect(() => {
    desktopViewPromise.then((Component) => setDesktopView(() => Component));
    mobileViewPromise.then((Component) => setMobileView(() => Component));
  }, []);

  // Check if mobile
  const prefix = `/${getBaseUrl().replace(/^\/+|\/+$/g, '')}`;
  const relativePath = pathname.startsWith(`${prefix}/`)
    ? pathname.slice(prefix.length)
    : pathname;
  // The responsive partner and its login flow remain reachable on phones.
  // Other business routes retain the site's existing mobile policy.
  const responsiveRoute =
    /^\/(assistant|login|logged-in|logout|register|mfa|mfa-setup|provider-signup|change-password|reset-password|set-password|verify-email)(\/|$)/.test(
      relativePath
    );
  const isMobile =
    !responsiveRoute &&
    !allowMobile &&
    window.INVENTREE_SETTINGS.mobile_mode !== 'allow-always' &&
    (width < 425 || height < 425);

  const View = isMobile ? MobileView : DesktopView;

  if (!View) {
    return null;
  }

  return <View />;
}
