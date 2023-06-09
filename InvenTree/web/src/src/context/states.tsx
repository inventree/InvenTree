export interface Host {
  host: string;
  name: string;
}

export interface HostList {
  [key: string]: Host;
}

export interface UserProps {
  name: string;
  email: string;
  username: string;
}

export interface ServerAPIProps {
  server: null | string;
  version: null | string;
  instance: null | string;
  apiVersion: null | number;
  worker_running: null | boolean;
  worker_pending_tasks: null | number;
  plugins_enabled: null | boolean;
  active_plugins: PluginProps[];
}

export interface PluginProps {
  name: string;
  slug: string;
  version: null | string;
}


// settings
export interface Setting {
  pk: number;
  key: string;
  value: string;
  name: string;
  description: string;
  type: SettingType;
  choices: SettingChoice[];
  model_name: null;
  api_url: null;
  typ: SettingTyp;
  plugin?: string;
  method?: string;
}

export interface SettingChoice {
  value: string;
  display_name: string;
}

export enum SettingTyp {
  Inventree = "inventree",
  Plugin = "plugin",
  User = "user",
  Notification = "notification",
}

export enum SettingType {
  Boolean = "boolean",
  Integer = "integer",
  String = "string",
}

// Errors
export type ErrorResponse = {
  data: any;
  status: number;
  statusText: string;
  message?: string;
};
