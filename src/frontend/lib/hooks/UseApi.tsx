import { useContext } from 'react';

import { ApiContext } from '../contexts/ApiContext';

export const useApi = () => {
  const context = useContext(ApiContext);

  if (!context) {
    throw new Error('useApi must be used within an ApiProvider');
  }

  return context;
};
