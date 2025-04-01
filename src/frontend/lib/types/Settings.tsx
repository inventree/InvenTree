export interface SettingChoice {
  value: string;
  display_name: string;
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
}

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

export type SettingsLookup = {
  [key: string]: string;
};
