import { QueryClientProvider } from '@tanstack/react-query';

import { queryClient } from '../App';
import { LanguageContext } from './LanguageContext';
import { ThemeContext } from './ThemeContext';

export const BaseContext = ({ children }: { children: any }) => {
  return (
    <QueryClientProvider client={queryClient}>
      <LanguageContext>
        <ThemeContext>{children}</ThemeContext>
      </LanguageContext>
    </QueryClientProvider>
  );
};
