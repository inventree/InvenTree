import { LanguageContext } from './LanguageContext';
import { ThemeContext } from './ThemeContext';

export const BaseContext = ({ children }: { children: any }) => {
  return (
    <LanguageContext>
      <ThemeContext>{children}</ThemeContext>
    </LanguageContext>
  );
};
