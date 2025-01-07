import { type QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { AxiosInstance } from 'axios';
import { createContext, useContext } from 'react';

const ApiContext = createContext<AxiosInstance | null>(null);

export const ApiProvider = ({
  api,
  client,
  children
}: {
  api: AxiosInstance;
  client: QueryClient;
  children: React.ReactNode;
}) => {
  return (
    <QueryClientProvider client={client}>
      <ApiContext.Provider value={api}>{children}</ApiContext.Provider>
    </QueryClientProvider>
  );
};

export const useApi = () => {
  const context = useContext(ApiContext);

  if (!context) {
    throw new Error('useApi must be used within an ApiProvider');
  }

  return context;
};
