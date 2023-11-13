import { MantineNumberSize } from '@mantine/core';
import { LoaderType } from '@mantine/styles/lib/theme/types/MantineTheme';
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

import { Locales } from '../contexts/LanguageContext';
import { HostList } from './states';

interface LocalStateProps {
  autoupdate: boolean;
  toggleAutoupdate: () => void;
  host: string;
  setHost: (newHost: string, newHostKey: string) => void;
  hostKey: string;
  hostList: HostList;
  setHostList: (newHostList: HostList) => void;
  language: Locales;
  setLanguage: (newLanguage: Locales) => void;
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
      hostKey: '',
      hostList: {},
      setHostList: (newHostList) => set({ hostList: newHostList }),
      language: 'en',
      setLanguage: (newLanguage) => set({ language: newLanguage }),
      //theme
      primaryColor: 'indigo',
      whiteColor: '#fff',
      blackColor: '#000',
      radius: 'xs',
      loader: 'oval'
    }),
    {
      name: 'session-settings'
    }
  )
);
