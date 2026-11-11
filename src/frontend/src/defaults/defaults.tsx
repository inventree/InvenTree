import type { MantineRadius } from '@mantine/core';

export const emptyServerAPI = {
  server: null,
  version: null,
  instance: null,
  apiVersion: null,
  plugins_enabled: null,
  active_plugins: [],
  system_health: null,
  default_locale: null,
  settings: null,
  customize: null
};

export interface SiteMarkProps {
  value: number;
  label: MantineRadius;
}

export const SizeMarks: SiteMarkProps[] = [
  { value: 0, label: 'xs' },
  { value: 25, label: 'sm' },
  { value: 50, label: 'md' },
  { value: 75, label: 'lg' },
  { value: 100, label: 'xl' }
];

export const frontendID = '706f6f7062757474';
export const serviceName = 'FRONTEND';
