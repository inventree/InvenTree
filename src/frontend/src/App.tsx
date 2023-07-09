import { useViewportSize } from '@mantine/hooks';
import { QueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { lazy } from 'react';

import { Loadable } from './Loading';
import { useLocalState } from './context/LocalState';
import { useSessionState } from './context/SessionState';

// API
export const api = axios.create({});
export function setApiDefaults() {
  const host = useLocalState.getState().host;
  const token = useSessionState.getState().token;

  api.defaults.baseURL = host;
  api.defaults.headers.common['Authorization'] = `Token ${token}`;
}
export const queryClient = new QueryClient();

function checkMobile() {
  const { height, width } = useViewportSize();
  if (width < 425 || height < 425) return true;
  return false;
}

// Main App
export default function App() {
  // Check if mobile
  if (checkMobile()) {
    const MobileAppView = Loadable(lazy(() => import('./MobileAppView')));
    return <MobileAppView />;
  }

  // Main App component
  const DesktopAppView = Loadable(lazy(() => import('./DesktopAppView')));
  return <DesktopAppView />;
}
