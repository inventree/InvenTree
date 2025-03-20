import { useContext } from 'react';

import type { AxiosInstance } from 'axios';
import { ApiContext } from '../contexts/ApiContext';

export const useApi = (): AxiosInstance => {
  const context = useContext(ApiContext);

  if (!context) {
    throw new Error('useApi must be used within an ApiProvider');
  }

  return context;
};
