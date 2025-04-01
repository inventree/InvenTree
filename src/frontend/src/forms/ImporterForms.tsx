import type { ApiFormFieldSet } from '@lib/forms';

export function dataImporterSessionFields(): ApiFormFieldSet {
  return {
    data_file: {},
    model_type: {},
    field_defaults: {
      hidden: true,
      value: {}
    },
    field_overrides: {
      hidden: true,
      value: {}
    },
    field_filters: {
      hidden: true,
      value: {}
    }
  };
}
