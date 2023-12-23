import { QueryClient } from '@tanstack/react-query';
import axios from 'axios';

import { useLocalState } from './states/LocalState';
import { useSessionState } from './states/SessionState';

// API
export const api = axios.create({});

export function setApiDefaults() {
  const host = useLocalState.getState().host;
  const token = useSessionState.getState().token;

  api.defaults.baseURL = host;
  api.defaults.headers.common['Authorization'] = `Token ${token}`;
}
export const queryClient = new QueryClient();
