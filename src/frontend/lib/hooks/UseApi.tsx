import { ApiContext } from '@lib/contexts/ApiContext';
import { useContext } from 'react';

export const useApi = () => {
  const context = useContext(ApiContext);

  if (!context) {
    throw new Error('useApi must be used within an ApiProvider');
  }

  return context;
};
