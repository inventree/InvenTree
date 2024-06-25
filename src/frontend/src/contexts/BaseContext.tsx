import { QueryClientProvider } from '@tanstack/react-query';

import { queryClient } from '../App';
import { ThemeContext } from './ThemeContext';

export const BaseContext = ({ children }: { children: any }) => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeContext>{children}</ThemeContext>
    </QueryClientProvider>
  );
};
