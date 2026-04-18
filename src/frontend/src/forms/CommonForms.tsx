import { IconUsers } from '@tabler/icons-react';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import type { ApiFormFieldSet } from '@lib/types/Forms';
import { t } from '@lingui/core/macro';
import type {
  StatusCodeInterface,
  StatusCodeListInterface
} from '../components/render/StatusRenderer';
import { useApi } from '../contexts/ApiContext';
import { useGlobalStatusState } from '../states/GlobalStatusState';

export function projectCodeFields(): ApiFormFieldSet {
  return {
    code: {},
    description: {},
    responsible: {
      icon: <IconUsers />
    }
  };
}

export function useCustomStateFields(): ApiFormFieldSet {
  // Status codes
  const statusCodes = useGlobalStatusState();

  // Selected base status class
  const [statusClass, setStatusClass] = useState<string>('');

  // Construct a list of status options based on the selected status class
  const statusOptions: any[] = useMemo(() => {
    const options: any[] = [];

    const valuesList = Object.values(statusCodes.status ?? {}).find(
      (value: StatusCodeListInterface) => value.status_class === statusClass
    );

    Object.values(valuesList?.values ?? {}).forEach(
      (value: StatusCodeInterface) => {
        options.push({
          value: value.key,
          display_name: value.label
        });
      }
    );

    return options;
  }, [statusCodes, statusClass]);

  return useMemo(() => {
    return {
      reference_status: {
        onValueChange(value) {
          setStatusClass(value);
        }
      },
      logical_key: {
        field_type: 'choice',
        choices: statusOptions
      },
      key: {},
      name: {},
      label: {},
      color: {},
      model: {}
    };
  }, [statusOptions]);
}

export function customUnitsFields(): ApiFormFieldSet {
  return {
    name: {},
    definition: {},
    symbol: {}
  };
}

export function extraLineItemFields(): ApiFormFieldSet {
  return {
    order: {
      hidden: true
    },
    line: {},
    reference: {},
    description: {},
    quantity: {},
    price: {},
    price_currency: {},
    project_code: {
      description: t`Select project code for this line item`
    },
    notes: {},
    link: {}
  };
}

export function useParameterFields({
  modelType,
  modelId
}: {
  modelType: ModelType;
  modelId: number;
}): ApiFormFieldSet {
  const api = useApi();

  const [selectionListId, setSelectionListId] = useState<number | null>(null);

  // Valid field choices
  const [choices, setChoices] = useState<any[]>([]);

  // Field type for "data" input
  const [fieldType, setFieldType] = useState<
    'string' | 'boolean' | 'choice' | 'related field'
  >('string');

  // Memoized value for the "data" field
  const [data, setData] = useState<string>('');

  const fetchSelectionEntry = useCallback(
    (value: any) => {
      if (!value || !selectionListId) {
        return null;
      }

      return api
        .get(apiUrl(ApiEndpoints.selectionentry_list, selectionListId), {
          params: {
            value: value
          }
        })
        .then((response) => {
          if (response.data && response.data.length == 1) {
            return response.data[0];
          } else {
            return null;
          }
        });
    },
    [selectionListId]
  );

  // Reset the field type and choices when the model changes
  useEffect(() => {
    setSelectionListId(null);
    setFieldType('string');
    setChoices([]);
    setData('');
  }, [modelType, modelId]);

  return useMemo(() => {
    return {
      model_type: {
        hidden: true,
        value: modelType
      },
      model_id: {
        hidden: true,
        value: modelId
      },
      template: {
        filters: {
          for_model: modelType,
          enabled: true
        },
        onValueChange: (value: any, record: any) => {
          setSelectionListId(record?.selectionlist || null);

          // Adjust the type of the "data" field based on the selected template
          if (record?.checkbox) {
            // This is a "checkbox" field
            setChoices([]);
            setFieldType('boolean');
          } else if (record?.choices) {
            const _choices: string[] = record.choices.split(',');

            if (_choices.length > 0) {
              setChoices(
                _choices.map((choice) => {
                  return {
                    display_name: choice.trim(),
                    value: choice.trim()
                  };
                })
              );
              setFieldType('choice');
            } else {
              setChoices([]);
              setFieldType('string');
            }
          } else if (record?.selectionlist) {
            setFieldType('related field');
          }
        }
      },
      data: {
        value: data,
        onValueChange: (value: any, record: any) => {
          if (fieldType === 'related field' && selectionListId) {
            // For related fields, we need to store the selected primary key value (not the string representation)
            setData(record?.value ?? value);
          } else {
            setData(value);
          }
        },
        type: fieldType,
        field_type: fieldType,
        choices: fieldType === 'choice' ? choices : undefined,
        default: fieldType === 'boolean' ? false : undefined,
        pk_field:
          fieldType === 'related field' && selectionListId
            ? 'value'
            : undefined,
        model:
          fieldType === 'related field' && selectionListId
            ? ModelType.selectionentry
            : undefined,
        api_url:
          fieldType === 'related field' && selectionListId
            ? apiUrl(ApiEndpoints.selectionentry_list, selectionListId)
            : undefined,
        filters:
          fieldType === 'related field'
            ? {
                active: true
              }
            : undefined,
        adjustValue: (value: any) => {
          // Coerce boolean value into a string (required by backend)

          let v: string = value.toString().trim();

          if (fieldType === 'boolean') {
            if (v.toLowerCase() !== 'true') {
              v = 'false';
            }
          }

          return v;
        },
        singleFetchFunction: fetchSelectionEntry
      },
      note: {}
    };
  }, [data, modelType, fieldType, choices, modelId, selectionListId]);
}
