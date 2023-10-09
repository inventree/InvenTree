import { QueryClientProvider } from '@tanstack/react-query';

import { queryClient } from '../App';
import { LanguageContext } from './LanguageContext';
import { ThemeContext } from './ThemeContext';
import { InvenTreeUserContext } from './UserContext';

export const BaseContext = ({ children }: { children: any }) => {
  return (
    <QueryClientProvider client={queryClient}>
      <LanguageContext>
        <InvenTreeUserContext>
          <ThemeContext>{children}</ThemeContext>
        </InvenTreeUserContext>
      </LanguageContext>
    </QueryClientProvider>
  );
};
