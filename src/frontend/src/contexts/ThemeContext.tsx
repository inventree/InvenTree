import { t } from '@lingui/macro';
import { MantineProvider, createTheme } from '@mantine/core';
import { ModalsProvider } from '@mantine/modals';
import { Notifications } from '@mantine/notifications';
import { ContextMenuProvider } from 'mantine-contextmenu';

import { useLocalState } from '@lib/index';
import { AboutInvenTreeModal } from '../components/modals/AboutInvenTreeModal';
import { LicenseModal } from '../components/modals/LicenseModal';
import { QrModal } from '../components/modals/QrModal';
import { ServerInfoModal } from '../components/modals/ServerInfoModal';
import { LanguageContext } from './LanguageContext';
import { colorSchema } from './colorSchema';

export function ThemeContext({
  children
}: Readonly<{ children: JSX.Element }>) {
  const [userTheme] = useLocalState((state) => [state.userTheme]);

  // Theme
  const myTheme = createTheme({
    primaryColor: userTheme.primaryColor,
    white: userTheme.whiteColor,
    black: userTheme.blackColor,
    defaultRadius: userTheme.radius,
    breakpoints: {
      xs: '30em',
      sm: '48em',
      md: '64em',
      lg: '74em',
      xl: '90em'
    }
  });

  return (
    <MantineProvider theme={myTheme} colorSchemeManager={colorSchema}>
      <ContextMenuProvider>
        <LanguageContext>
          <ModalsProvider
            labels={{ confirm: t`Submit`, cancel: t`Cancel` }}
            modals={{
              info: ServerInfoModal,
              about: AboutInvenTreeModal,
              license: LicenseModal,
              qr: QrModal
            }}
          >
            <Notifications />
            {children}
          </ModalsProvider>
        </LanguageContext>
      </ContextMenuProvider>
    </MantineProvider>
  );
}
