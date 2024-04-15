import { t } from '@lingui/macro';
import {
  MantineProvider,
  createTheme,
  localStorageColorSchemeManager
} from '@mantine/core';
import { useColorScheme } from '@mantine/hooks';
import { ModalsProvider } from '@mantine/modals';
import { Notifications } from '@mantine/notifications';

import { AboutInvenTreeModal } from '../components/modals/AboutInvenTreeModal';
import { LicenseModal } from '../components/modals/LicenseModal';
import { QrCodeModal } from '../components/modals/QrCodeModal';
import { ServerInfoModal } from '../components/modals/ServerInfoModal';
import { useLocalState } from '../states/LocalState';

export function ThemeContext({ children }: { children: JSX.Element }) {
  const [primaryColor, whiteColor, blackColor, radius] = useLocalState(
    (state) => [
      state.primaryColor,
      state.whiteColor,
      state.blackColor,
      state.radius
    ]
  );

  // Color Scheme
  const preferredColorScheme = useColorScheme();
  const colorSchemeManager = localStorageColorSchemeManager({
    key: 'scheme'
  });

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
    <MantineProvider
      theme={myTheme}
      defaultColorScheme={preferredColorScheme}
      colorSchemeManager={colorSchemeManager}
    >
      <Notifications />
      <ModalsProvider
        labels={{ confirm: t`Submit`, cancel: t`Cancel` }}
        modals={{
          qr: QrCodeModal,
          info: ServerInfoModal,
          about: AboutInvenTreeModal,
          license: LicenseModal
        }}
      >
        {children}
      </ModalsProvider>
    </MantineProvider>
  );
}
