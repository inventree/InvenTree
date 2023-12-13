import { useViewportSize } from '@mantine/hooks';
import { QueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { lazy } from 'react';

import { Loadable } from './functions/loading';
import { useLocalState } from './states/LocalState';
import { useSessionState } from './states/SessionState';

// API
export const api = axios.create({});

export function setApiDefaults() {
  const host = useLocalState.getState().host;
  const token = useSessionState.getState().token;

  api.defaults.baseURL = host;

  if (token) {
    api.defaults.headers.common['Authorization'] = `Token ${token}`;
  } else {
    api.defaults.headers.common['Authorization'] = null;
  }
}

export const queryClient = new QueryClient();

function checkMobile() {
  const { height, width } = useViewportSize();
  if (width < 425 || height < 425) return true;
  return false;
}

const MobileAppView = Loadable(lazy(() => import('./views/MobileAppView')));
const DesktopAppView = Loadable(lazy(() => import('./views/DesktopAppView')));

// Main App
export default function App() {
  // Check if mobile
  if (checkMobile()) {
    return <MobileAppView />;
  }

  // Main App component
  return <DesktopAppView />;
}
