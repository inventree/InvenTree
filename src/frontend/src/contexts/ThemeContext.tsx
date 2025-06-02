import { msg } from '@lingui/core/macro';
import { Trans } from '@lingui/react';
import { MantineProvider, createTheme } from '@mantine/core';
import { ModalsProvider } from '@mantine/modals';
import { Notifications } from '@mantine/notifications';
import { ContextMenuProvider } from 'mantine-contextmenu';
import { useShallow } from 'zustand/react/shallow';
import { AboutInvenTreeModal } from '../components/modals/AboutInvenTreeModal';
import { LicenseModal } from '../components/modals/LicenseModal';
import { QrModal } from '../components/modals/QrModal';
import { ServerInfoModal } from '../components/modals/ServerInfoModal';
import { useLocalState } from '../states/LocalState';
import { LanguageContext } from './LanguageContext';
import { colorSchema } from './colorSchema';

import type { JSX } from 'react';

export function ThemeContext({
  children
}: Readonly<{ children: JSX.Element }>) {
  const [userTheme] = useLocalState(useShallow((state) => [state.userTheme]));

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
