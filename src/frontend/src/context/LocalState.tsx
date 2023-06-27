import { MantineNumberSize } from '@mantine/core';
import { LoaderType } from '@mantine/styles/lib/theme/types/MantineTheme';
import create from 'zustand';
import { persist } from 'zustand/middleware';
import { Locales } from './LanguageContext';
import { HostList } from './states';

interface LocalStateProps {
  autoupdate: boolean;
  toggleAutoupdate: () => void;
  host: string;
  setHost: (newHost: string, newHostKey: string) => void;
  hostKey: string;
  hostList: HostList;
  lastUsername: string;
  language: Locales;
  // theme
  primaryColor: string;
  whiteColor: string;
  blackColor: string;
  radius: MantineNumberSize;
  loader: LoaderType;
}

export const useLocalState = create<LocalStateProps>()(
  persist(
    (set) => ({
      autoupdate: false,
      toggleAutoupdate: () =>
        set((state) => ({ autoupdate: !state.autoupdate })),
      host: '',
      setHost: (newHost, newHostKey) =>
        set({ host: newHost, hostKey: newHostKey }),
      lastUsername: '',
      hostKey: '',
      hostList: {},
      language: 'en',
      //theme
      primaryColor: 'indigo',
      whiteColor: '#fff',
      blackColor: '#000',
      radius: 'md',
      loader: 'oval'
    }),
    {
      name: 'session-settings'
    }
  )
);
