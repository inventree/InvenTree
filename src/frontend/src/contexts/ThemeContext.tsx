import { msg } from '@lingui/core/macro';
import { Trans } from '@lingui/react';
import {
  MantineProvider,
  type MantineThemeOverride,
  createTheme
} from '@mantine/core';
import { ModalsProvider } from '@mantine/modals';
import { Notifications } from '@mantine/notifications';
import { ContextMenuProvider } from 'mantine-contextmenu';
import { useShallow } from 'zustand/react/shallow';
import { useLocalState } from '../states/LocalState';
import { LanguageContext } from './LanguageContext';
import { colorSchema } from './colorSchema';

// Lazy load the various modal dialogs - they are not needed immediately, and this can help to reduce the initial bundle size
const AboutInvenTreeModal = lazy(() =>
  import('../components/modals/AboutInvenTreeModal').then((module) => ({
    default: module.AboutInvenTreeModal
  }))
);
const LicenseModal = lazy(() =>
  import('../components/modals/LicenseModal').then((module) => ({
    default: module.LicenseModal
  }))
);
const QrModal = lazy(() =>
  import('../components/modals/QrModal').then((module) => ({
    default: module.QrModal
  }))
);
const ServerInfoModal = lazy(() =>
  import('../components/modals/ServerInfoModal').then((module) => ({
    default: module.ServerInfoModal
  }))
);

import { type JSX, lazy } from 'react';

export function ThemeContext({
  children
}: Readonly<{ children: JSX.Element }>) {
  const [userTheme] = useLocalState(useShallow((state) => [state.userTheme]));

  let customUserTheme: MantineThemeOverride | undefined = undefined;

  // Theme
  try {
    customUserTheme = createTheme({
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
  } catch (error) {
    console.error('Error creating theme with user settings:', error);
    // Fallback to default theme if there's an error
    customUserTheme = undefined;
  }

  return (
    <MantineProvider theme={customUserTheme} colorSchemeManager={colorSchema}>
      <ContextMenuProvider>
        <LanguageContext>
          <ModalsProvider
            labels={{
              confirm: <Trans id={msg`Submit`.id} />,
              cancel: <Trans id={msg`Cancel`.id} />
            }}
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
