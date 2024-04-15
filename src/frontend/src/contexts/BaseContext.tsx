import { QueryClientProvider } from '@tanstack/react-query';

import { queryClient } from '../App';
import { LanguageContext } from './LanguageContext';
import { ThemeContext } from './ThemeContext';

export const BaseContext = ({ children }: { children: any }) => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeContext>
        <LanguageContext>{children}</LanguageContext>
      </ThemeContext>
    </QueryClientProvider>
  );
};
