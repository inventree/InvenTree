/**
 * This file is used to define the type(s) of available DetailsField components.
 */
import { ModelType } from '../../enums/ModelType';

export type BadgeType = 'owner' | 'user' | 'group';
type ValueFormatterReturn = string | number | null;

// Define type for rendering a simple "string" detail field
type StringDetailField = {
  type: 'string' | 'text';
  unit?: boolean;
};

// Link to another model instance
type InternalLinkField = {
  model: ModelType;
};

// Link to an external URL
type ExternalLinkField = {
  external: true;
};

// Define type for rendering a "link" detail field
type LinkDetailField = {
  type: 'link';
} & (InternalLinkField | ExternalLinkField);

type ProgressBarfield = {
  type: 'progressbar';
  progress: number;
  total: number;
};

export type FieldValueType = string | number | undefined;

export type DetailsField =
  | {
      name: string;
      label?: string;
      badge?: BadgeType;
      copy?: boolean;
      value_formatter?: () => ValueFormatterReturn;
    } & (StringDetailField | LinkDetailField | ProgressBarfield);

export type FieldProps = {
  field_data: any;
  field_value: string | number;
  unit?: string | null;
};
