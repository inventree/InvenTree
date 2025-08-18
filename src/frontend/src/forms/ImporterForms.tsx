import type { ApiFormFieldSet } from '@lib/types/Forms';

export function dataImporterSessionFields(): ApiFormFieldSet {
  return {
    data_file: {},
    model_type: {},
    update_records: {},
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
