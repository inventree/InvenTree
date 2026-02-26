import type { ApiEndpoints } from '../enums/ApiEndpoints';
import type { PathParams } from './Core';

export enum SettingTyp {
  InvenTree = 'inventree',
  Plugin = 'plugin',
  User = 'user',
  Notification = 'notification'
}

export enum SettingType {
  Boolean = 'boolean',
  Integer = 'integer',
  String = 'string',
  Choice = 'choice',
  Model = 'related field'
}

// Type interface defining a single 'setting' object
export interface Setting {
  pk: number;
  key: string;
  value: string;
  name: string;
  description: string;
  type: SettingType;
  units: string;
  choices: SettingChoice[];
  model_name: string | null;
  model_filters: Record<string, any> | null;
  api_url: string | null;
  typ: SettingTyp;
  plugin?: string;
  method?: string;
  required?: boolean;
  read_only?: boolean;
  confirm?: boolean;
  confirm_text?: string;
}

export interface SettingChoice {
  value: string;
  display_name: string;
}

export type SettingsLookup = {
  [key: string]: string;
};

export interface SettingsStateProps {
  settings: Setting[];
  lookup: SettingsLookup;
  fetchSettings: () => Promise<boolean>;
  loaded: boolean;
  isError: boolean;
  endpoint: ApiEndpoints;
  pathParams?: PathParams;
  getSetting: (key: string, default_value?: string) => string; // Return a raw setting value
  isSet: (key: string, default_value?: boolean) => boolean; // Check a "boolean" setting
}
