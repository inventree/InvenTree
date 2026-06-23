import {
  type MantineColorScheme,
  type MantineColorSchemeManager,
  isMantineColorScheme
} from '@mantine/core';

export interface LocalStorageColorSchemeManagerOptions {
  /** Local storage key used to retrieve value with `localStorage.getItem(key)`, `mantine-color-scheme` by default */
  key?: string;
}

export function localStorageColorSchemeManager({
  key = 'mantine-color-scheme'
}: LocalStorageColorSchemeManagerOptions = {}): MantineColorSchemeManager {
  let handleStorageEvent: (event: StorageEvent) => void;

  return {
    get: (defaultValue) => {
      if (typeof window === 'undefined') {
        return defaultValue;
      }

      try {
        const storedValue = window.localStorage.getItem(key);

        // If a value exists in storage, return it
        if (storedValue && isMantineColorScheme(storedValue)) {
          return storedValue;
        }

        // If no value, check the system preference
        const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        return systemPrefersDark ? 'dark' : 'light';
      } catch {
        return defaultValue;
      }
    },

    set: (value) => {
      try {
        window.localStorage.setItem(key, value);
      } catch (error) {
        // eslint-disable-next-line no-console
        console.warn(
          '[@mantine/core] Local storage color scheme manager was unable to save color scheme.',
          error
        );
      }
    },

    subscribe: (onUpdate) => {
      handleStorageEvent = (event) => {
        if (event.storageArea === window.localStorage && event.key === key) {
          isMantineColorScheme(event.newValue) && onUpdate(event.newValue);
        }
      };

      window.addEventListener('storage', handleStorageEvent);
    },

    unsubscribe: () => {
      window.removeEventListener('storage', handleStorageEvent);
    },

    clear: () => {
      window.localStorage.removeItem(key);
    }
  };
}

export const colorSchema = localStorageColorSchemeManager({
  key: 'scheme'
});
