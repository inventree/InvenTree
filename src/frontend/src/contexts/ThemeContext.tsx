import { t } from '@lingui/macro';
import { MantineProvider, createTheme } from '@mantine/core';
import { ModalsProvider } from '@mantine/modals';
import { Notifications } from '@mantine/notifications';

import { AboutInvenTreeModal } from '../components/modals/AboutInvenTreeModal';
import { LicenseModal } from '../components/modals/LicenseModal';
import { QrCodeModal } from '../components/modals/QrCodeModal';
import { ServerInfoModal } from '../components/modals/ServerInfoModal';
import { useLocalState } from '../states/LocalState';
import { LanguageContext } from './LanguageContext';
import { colorSchema } from './colorSchema';

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
