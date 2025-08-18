import type { ModelType } from '@lib/enums/ModelType';
import type { ApiFormFieldSet } from '@lib/types/Forms';

export function dataImporterSessionFields({
  modelType,
  allowUpdate = false
}: {
  modelType?: ModelType | string;
  allowUpdate?: boolean;
}): ApiFormFieldSet {
  return {
    data_file: {},
    model_type: {
      value: modelType,
      hidden: modelType != undefined
    },
    update_records: {
      hidden: allowUpdate != true,
      value: allowUpdate ? undefined : false
    },
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
