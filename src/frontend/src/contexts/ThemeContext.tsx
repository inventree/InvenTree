import { t } from '@lingui/macro';
import { MantineProvider, createTheme } from '@mantine/core';
import { ModalsProvider } from '@mantine/modals';
import { Notifications } from '@mantine/notifications';
import { lazy } from 'react';

import { useLocalState } from '../states/LocalState';
import { LanguageContext } from './LanguageContext';
import { colorSchema } from './colorSchema';

// Lazy load global modals
const AboutInvenTreeModal = lazy(
  () => import('../components/modals/AboutInvenTreeModal')
);

const LicenseModal = lazy(() => import('../components/modals/LicenseModal'));

const QrCodeModal = lazy(() => import('../components/modals/QrCodeModal'));

const ServerInfoModal = lazy(
  () => import('../components/modals/ServerInfoModal')
);

export function ThemeContext({ children }: { children: JSX.Element }) {
  const [primaryColor, whiteColor, blackColor, radius] = useLocalState(
    (state) => [
      state.primaryColor,
      state.whiteColor,
      state.blackColor,
      state.radius
    ]
  );

  // Theme
  const myTheme = createTheme({
    primaryColor: primaryColor,
    white: whiteColor,
    black: blackColor,
    defaultRadius: radius,
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
      <LanguageContext>
        <ModalsProvider
          labels={{ confirm: t`Submit`, cancel: t`Cancel` }}
          modals={{
            qr: QrCodeModal,
            info: ServerInfoModal,
            about: AboutInvenTreeModal,
            license: LicenseModal
          }}
        >
          <Notifications />
          {children}
        </ModalsProvider>
      </LanguageContext>
    </MantineProvider>
  );
}
