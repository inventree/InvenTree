import { MantineSize } from '@mantine/core';

export const emptyServerAPI = {
  server: null,
  version: null,
  instance: null,
  apiVersion: null,
  worker_running: null,
  worker_pending_tasks: null,
  plugins_enabled: null,
  active_plugins: []
};

export interface SiteMarkProps {
  value: number;
  label: MantineSize;
}

export const SizeMarks: SiteMarkProps[] = [
  { value: 0, label: 'xs' },
  { value: 25, label: 'sm' },
  { value: 50, label: 'md' },
  { value: 75, label: 'lg' },
  { value: 100, label: 'xl' }
];
