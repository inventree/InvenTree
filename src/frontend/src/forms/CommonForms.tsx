import { IconUsers } from '@tabler/icons-react';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import type { ApiFormFieldSet, ApiFormFieldType } from '@lib/types/Forms';
import type {
  StatusCodeInterface,
  StatusCodeListInterface
} from '../components/render/StatusRenderer';
import { useApi } from '../contexts/ApiContext';
import { useGlobalStatusState } from '../states/GlobalStatusState';
import { useUserState } from '../states/UserState';
import { ProjectCodeField } from './CommonFields';

export function projectCodeFields(): ApiFormFieldSet {
  return {
    code: {},
    description: {},
    responsible: {
      icon: <IconUsers />
    },
    active: {}
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
    project_code: ProjectCodeField(),
    notes: {},
    link: {}
  };
}

export function useParameterTemplateFields(): ApiFormFieldSet {
  return useMemo(() => {
    return {
      name: {},
      description: {},
      units: {},
      model_type: {},
      choices: {},
      checkbox: {},
      selectionlist: {
        filters: {
          active: true
        }
      },
      enabled: {}
    };
  }, []);
}

/**
 * Shared hook for the dynamic "value" field on parameter forms.
 *
 * When the user selects a parameter template, the field type for the
 * corresponding value input (data / default_value) must change to match the
 * template's data type (boolean, choice, related-field selection list, or
 * plain string).  This hook encapsulates that state so it can be reused
 * across the "Add Parameter" and "Add Category Parameter" forms.
 *
 * @param resetDep - When this value changes all internal state is reset to
 *   defaults.  Pass a stringified key derived from the form's context (e.g.
 *   `${modelType}-${modelId}`) so the field resets when the context switches.
 */
export function useDynamicParameterValueField(resetDep?: any): {
  onTemplateValueChange: (value: any, record: any) => void;
  valueFieldConfig: ApiFormFieldType;
  reset: () => void;
} {
  const api = useApi();

  const [selectionListId, setSelectionListId] = useState<number | null>(null);
  const [choices, setChoices] = useState<any[]>([]);
  const [fieldType, setFieldType] = useState<
    'string' | 'boolean' | 'choice' | 'related field'
  >('string');
  const [data, setData] = useState<string>('');

  const reset = useCallback(() => {
    setSelectionListId(null);
    setFieldType('string');
    setChoices([]);
    setData('');
  }, []);

  useEffect(() => {
    reset();
  }, [resetDep, reset]);

  const fetchSelectionEntry = useCallback(
    (value: any) => {
      if (!value || !selectionListId) {
        return null;
      }

      return api
        .get(apiUrl(ApiEndpoints.selectionentry_list, selectionListId), {
          params: { value: value }
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

  const onTemplateValueChange = useCallback(
    (value: any, record: any) => {
      setSelectionListId(record?.selectionlist || null);
      setData('');

      if (record?.checkbox) {
        setChoices([]);
        setFieldType('boolean');
        setData('false');
      } else if (record?.choices) {
        const _choices: string[] = record.choices.split(',');

        if (_choices.length > 0) {
          setChoices(
            _choices.map((choice) => ({
              display_name: choice.trim(),
              value: choice.trim()
            }))
          );
          setFieldType('choice');
        } else {
          setChoices([]);
          setFieldType('string');
          setData('');
        }
      } else if (record?.selectionlist) {
        setFieldType('related field');
        setData('');
      } else {
        setFieldType('string');
        setData('');
      }
    },
    [setFieldType, setData, setChoices]
  );

  const valueFieldConfig: ApiFormFieldType = useMemo(
    () => ({
      value: data,
      onValueChange: (value: any, record: any) => {
        if (fieldType === 'related field' && selectionListId) {
          // For related fields, store the primary key value (not the string representation)
          setData(record?.value ?? value);
        } else {
          setData(value);
        }
      },
      field_type: fieldType,
      choices: fieldType === 'choice' ? choices : undefined,
      default: fieldType === 'boolean' ? false : undefined,
      pk_field:
        fieldType === 'related field' && selectionListId ? 'value' : undefined,
      model:
        fieldType === 'related field' && selectionListId
          ? ModelType.selectionentry
          : undefined,
      api_url:
        fieldType === 'related field' && selectionListId
          ? apiUrl(ApiEndpoints.selectionentry_list, selectionListId)
          : undefined,
      filters: fieldType === 'related field' ? { active: true } : undefined,
      adjustValue: (value: any) => {
        let v: string = value.toString().trim();

        if (fieldType === 'boolean') {
          if (v.toLowerCase() !== 'true') {
            v = 'false';
          }
        }

        return v;
      },
      singleFetchFunction: fetchSelectionEntry
    }),
    [data, fieldType, choices, selectionListId, fetchSelectionEntry]
  );

  return { onTemplateValueChange, valueFieldConfig, reset };
}

export function useParameterFields({
  modelType,
  modelId
}: {
  modelType: ModelType;
  modelId: number;
}): ApiFormFieldSet {
  const user = useUserState.getState();
  const templateCreateFields = useParameterTemplateFields();

  const resetKey = useMemo(
    () => `${modelType}-${modelId}`,
    [modelType, modelId]
  );
  const { onTemplateValueChange, valueFieldConfig } =
    useDynamicParameterValueField(resetKey);

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
        onValueChange: onTemplateValueChange,
        addCreateFields: user.isStaff() ? templateCreateFields : undefined
      },
      data: valueFieldConfig,
      note: {}
    };
  }, [
    modelType,
    modelId,
    onTemplateValueChange,
    valueFieldConfig,
    templateCreateFields,
    user
  ]);
}

export function useNoteTemplateFields(): ApiFormFieldSet {
  return useMemo(() => {
    return {
      template: {
        hidden: true,
        value: true
      },
      model_type: {
        label: t`Model Type`,
        description: t`Limit this template to a specific model type, or leave blank for all models`,
        required: false
      },
      title: {},
      description: {}
    };
  }, []);
}

export function useNoteFields({
  modelType,
  modelId
}: {
  modelType: ModelType;
  modelId: number;
}): ApiFormFieldSet {
  const api = useApi();

  const [title, setTitle] = useState<string>('');
  const [description, setDescription] = useState<string>('');
  const [content, setContent] = useState<string>('');

  const fetchTemplate = useCallback(
    (pk: number | null) => {
      if (!pk) return;
      api
        .get(apiUrl(ApiEndpoints.note_list, pk))
        .then((response) => {
          setTitle(response.data.title ?? '');
          setDescription(response.data.description ?? '');
          setContent(response.data.content ?? '');
        })
        .catch(() => {});
    },
    [api]
  );

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
      template_source: {
        field_type: 'related field',
        label: t`From Template`,
        description: t`Optionally pre-fill this note from an existing template`,
        model: ModelType.notetemplate,
        api_url: apiUrl(ApiEndpoints.note_list),
        filters: {
          template: true,
          model_type: modelType
        },
        pk_field: 'pk',
        required: false,
        onValueChange: (value: any) => fetchTemplate(value),
        value: null
      },
      title: {
        value: title,
        onValueChange: (value: any) => setTitle(value)
      },
      description: {
        value: description,
        onValueChange: (value: any) => setDescription(value)
      },
      primary: {},
      content: {
        hidden: true,
        value: content
      }
    };
  }, [modelType, modelId, title, description, content, fetchTemplate]);
}

export function selectionListFields(): ApiFormFieldSet {
  return {
    name: {},
    description: {},
    active: {},
    source_plugin: {},
    source_string: {}
  };
}

export function selectionEntryFields(): ApiFormFieldSet {
  return {
    value: {},
    label: {},
    description: {},
    active: {}
  };
}
