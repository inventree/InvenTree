import { useMemo } from 'react';

import { ApiFormFieldSet } from '../components/forms/fields/ApiFormField';

export function dataImporterSessionFields({ model }: { model: string }) {
  return useMemo(() => {
    const fields: ApiFormFieldSet = {
      data_file: {},
      model_type: {
        value: model
      },
      field_detauls: {
        hidden: true
      }
    };

    return fields;
  }, []);
}
