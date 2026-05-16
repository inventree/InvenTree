import type { MantineRadius } from '@mantine/core';

export const emptyServerAPI = {
  server: null,
  version: null,
  instance: null,
  apiVersion: null,
  worker_running: null,
  worker_pending_tasks: null,
  plugins_enabled: null,
  plugins_install_disabled: null,
  active_plugins: [],
  email_configured: null,
  debug_mode: null,
  docker_mode: null,
  database: null,
  system_health: null,
  platform: null,
  installer: null,
  target: null,
  default_locale: null,
  django_admin: null,
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
