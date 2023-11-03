import { t } from '@lingui/macro';
import {
  ColorScheme,
  ColorSchemeProvider,
  MantineProvider,
  MantineThemeOverride
} from '@mantine/core';
import { useColorScheme, useLocalStorage } from '@mantine/hooks';
import { ModalsProvider } from '@mantine/modals';
import { Notifications } from '@mantine/notifications';

import { AboutInvenTreeModal } from '../components/modals/AboutInvenTreeModal';
import { QrCodeModal } from '../components/modals/QrCodeModal';
import { ServerInfoModal } from '../components/modals/ServerInfoModal';
import { useLocalState } from '../states/LocalState';

export function ThemeContext({ children }: { children: JSX.Element }) {
  const [primaryColor, whiteColor, blackColor, radius, loader] = useLocalState(
    (state) => [
      state.primaryColor,
      state.whiteColor,
      state.blackColor,
      state.radius,
      state.loader
    ]
  );

  // Color Scheme
  const preferredColorScheme = useColorScheme();
  const [colorScheme, setColorScheme] = useLocalStorage<ColorScheme>({
    key: 'scheme',
    defaultValue: preferredColorScheme
  });
  const toggleColorScheme = (value?: ColorScheme) => {
    setColorScheme(value || (colorScheme === 'dark' ? 'light' : 'dark'));
    myTheme.colorScheme = colorScheme;
  };

  // Theme
  const myTheme: MantineThemeOverride = {
    colorScheme: colorScheme,
    primaryColor: primaryColor,
    white: whiteColor,
    black: blackColor,
    loader: loader,
    defaultRadius: radius,
    breakpoints: {
      xs: '30em',
      sm: '48em',
      md: '64em',
      lg: '74em',
      xl: '90em'
    }
  };

  return (
    <ColorSchemeProvider
      colorScheme={colorScheme}
      toggleColorScheme={toggleColorScheme}
    >
      <MantineProvider theme={myTheme} withGlobalStyles withNormalizeCSS>
        <Notifications />
        <ModalsProvider
          labels={{ confirm: t`Submit`, cancel: t`Cancel` }}
          modals={{
            qr: QrCodeModal,
            info: ServerInfoModal,
            about: AboutInvenTreeModal
          }}
        >
          {children}
        </ModalsProvider>
      </MantineProvider>
    </ColorSchemeProvider>
  );
}
