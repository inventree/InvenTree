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
export interface GlobalSetting {
  pk: number;
  key: string;
  value: string;
  name: string;
  description: string;
  type: Type;
  choices: Choice[];
  model_name: null;
  api_url: null;
  typ: Typ;
}

export interface Choice {
  value: string;
  display_name: string;
}

export enum Typ {
  Inventree = "inventree",
}

export enum Type {
  Boolean = "boolean",
  Integer = "integer",
  String = "string",
}
