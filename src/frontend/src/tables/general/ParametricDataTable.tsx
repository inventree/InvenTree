import { cancelEvent } from '@lib/functions/Events';
import {
  ApiEndpoints,
  type ApiFormFieldSet,
  type ModelType,
  UserRoles,
  YesNoButton,
  apiUrl,
  formatDecimal,
  getDetailUrl,
  navigateToLink
} from '@lib/index';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { t } from '@lingui/core/macro';
import { Group } from '@mantine/core';
import { useHover } from '@mantine/hooks';
import { IconCirclePlus } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { type ReactNode, useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApi } from '../../contexts/ApiContext';
import { useParameterFields } from '../../forms/CommonForms';
import {
  useCreateApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import { InvenTreeTable } from '../InvenTreeTable';
import { TableHoverCard } from '../TableHoverCard';
import {
  PARAMETER_FILTER_OPERATORS,
  ParameterFilter
} from './ParametricDataTableFilters';

// Render an individual parameter cell
function ParameterCell({
  record,
  template,
  canEdit
}: Readonly<{
  record: any;
  template: any;
  canEdit: boolean;
}>) {
  const { hovered, ref } = useHover();

  // Find matching template parameter
  const parameter = useMemo(() => {
    return record.parameters?.find((p: any) => p.template == template.pk);
  }, [record, template]);

  const extra: any[] = [];

  // Format the value for display
  const value: ReactNode = useMemo(() => {
    let v: any = parameter?.data;

    // Handle boolean values
    if (template?.checkbox && v != undefined) {
      v = <YesNoButton value={parameter.data} />;
    }

    return v;
  }, [parameter, template]);

  if (
    template.units &&
    parameter &&
    parameter.data_numeric &&
    parameter.data_numeric != parameter.data
  ) {
    const numeric = formatDecimal(parameter.data_numeric, { digits: 15 });
    extra.push(`${numeric} [${template.units}]`);
  }

  if (hovered && canEdit) {
    extra.push(t`Click to edit`);
  }

  return (
    <div>
      <Group grow ref={ref} justify='space-between'>
        <Group grow>
          <TableHoverCard
            value={value ?? '-'}
            extra={extra}
            icon={hovered && canEdit ? 'edit' : 'info'}
            title={template.name}
          />
        </Group>
      </Group>
    </div>
  );
}

/**
 * A table which displays parametric data for generic model types.
 * The table can be extended by passing in additional column, filters, and actions.
 */
export default function ParametricDataTable({
  modelType,
  endpoint,
  queryParams,
  customFilters,
  customColumns
}: {
  modelType: ModelType;
  endpoint: ApiEndpoints | string;
  queryParams?: Record<string, any>;
  customFilters?: TableFilter[];
  customColumns?: TableColumn[];
}) {
  const api = useApi();
  const table = useTable(`parametric-data-${modelType}`);
  const user = useUserState();
  const navigate = useNavigate();

  // Fetch all active parameter templates for the given model type
  const parameterTemplates = useQuery({
    queryKey: ['parameter-templates', modelType],
    queryFn: async () => {
      return api
        .get(apiUrl(ApiEndpoints.parameter_template_list), {
          params: {
            active: true,
            for_model: modelType,
            exists_for_model: modelType
          }
        })
        .then((response) => response.data);
    },
    refetchOnMount: true
  });

  /* Store filters against selected part parameters.
   * These are stored in the format:
   * {
   *   parameter_1: {
   *    '=': 'value1',
   *    '<': 'value2',
   *    ...
   *   },
   *   parameter_2: {
   *    '=': 'value3',
   *   },
   *   ...
   * }
   *
   * Which allows multiple filters to be applied against each parameter template.
   */
  const [parameterFilters, setParameterFilters] = useState<any>({});

  /* Remove filters for a specific parameter template
   * - If no operator is specified, remove all filters for this template
   * - If an operator is specified, remove filters for that operator only
   */
  const clearParameterFilter = useCallback(
    (templateId: number, operator?: string) => {
      const filterName = `parameter_${templateId}`;

      if (!operator) {
        // If no operator is specified, remove all filters for this template
        setParameterFilters((prev: any) => {
          const newFilters = { ...prev };
          // Remove any filters that match the template ID
          Object.keys(newFilters).forEach((key: string) => {
            if (key == filterName) {
              delete newFilters[key];
            }
          });
          return newFilters;
        });

        return;
      }

      // An operator is specified, so we remove filters for that operator only
      setParameterFilters((prev: any) => {
        const filters = { ...prev };

        const paramFilters = filters[filterName] || {};

        if (paramFilters[operator] !== undefined) {
          // Remove the specific operator filter
          delete paramFilters[operator];
        }

        return {
          ...filters,
          [filterName]: paramFilters
        };
      });

      table.refreshTable();
    },
    [setParameterFilters, table.refreshTable]
  );

  /**
   * Add (or update) a filter for a specific parameter template.
   * @param templateId - The ID of the parameter template to filter on.
   * @param value - The value to filter by.
   * @param operator - The operator to use for filtering (e.g., '=', '<', '>', etc.).
   */
  const addParameterFilter = useCallback(
    (templateId: number, value: string, operator: string) => {
      const filterName = `parameter_${templateId}`;

      const filterValue = value?.toString().trim() ?? '';

      if (filterValue.length > 0) {
        setParameterFilters((prev: any) => {
          const filters = { ...prev };
          const paramFilters = filters[filterName] || {};

          paramFilters[operator] = filterValue;

          return {
            ...filters,
            [filterName]: paramFilters
          };
        });

        table.refreshTable();
      }
    },
    [setParameterFilters, clearParameterFilter, table.refreshTable]
  );

  // Construct the query filters for the table based on the parameter filters
  const parametricQueryFilters = useMemo(() => {
    const filters: Record<string, string> = {};

    Object.keys(parameterFilters).forEach((key: string) => {
      const paramFilters: any = parameterFilters[key];

      Object.keys(paramFilters).forEach((operator: string) => {
        const name = `${key}${PARAMETER_FILTER_OPERATORS[operator] || ''}`;
        const value = paramFilters[operator];

        filters[name] = value;
      });
    });

    return filters;
  }, [parameterFilters]);

  const [selectedInstance, setSelectedInstance] = useState<number>(-1);
  const [selectedTemplate, setSelectedTemplate] = useState<number | null>(null);
  const [selectedParameter, setSelectedParameter] = useState<number>(-1);

  const parameterFields: ApiFormFieldSet = useParameterFields({
    modelType: modelType,
    modelId: selectedInstance
  });

  const addParameter = useCreateApiFormModal({
    url: ApiEndpoints.parameter_list,
    title: t`Add Parameter`,
    fields: useMemo(() => ({ ...parameterFields }), [parameterFields]),
    focus: 'data',
    onFormSuccess: (parameter: any) => {
      updateParameterRecord(selectedInstance, parameter);

      // Ensure that the parameter template is included in the table
      const template = parameterTemplates.data.find(
        (t: any) => t.pk == parameter.template
      );

      if (!template) {
        // Reload the parameter templates
        parameterTemplates.refetch();
      }
    },
    initialData: {
      part: selectedInstance,
      template: selectedTemplate
    }
  });

  const editParameter = useEditApiFormModal({
    url: ApiEndpoints.parameter_list,
    title: t`Edit Parameter`,
    pk: selectedParameter,
    fields: useMemo(() => ({ ...parameterFields }), [parameterFields]),
    focus: 'data',
    onFormSuccess: (parameter: any) => {
      updateParameterRecord(selectedInstance, parameter);
    }
  });

  // Update a single parameter record in the table
  const updateParameterRecord = useCallback(
    (part: number, parameter: any) => {
      const records = table.records;
      const recordIndex = records.findIndex((record: any) => record.pk == part);

      if (recordIndex < 0) {
        // No matching part: reload the entire table
        table.refreshTable();
        return;
      }

      const parameterIndex = records[recordIndex].parameters.findIndex(
        (p: any) => p.pk == parameter.pk
      );

      if (parameterIndex < 0) {
        // No matching parameter - append new parameter
        records[recordIndex].parameters.push(parameter);
      } else {
        records[recordIndex].parameters[parameterIndex] = parameter;
      }

      table.updateRecord(records[recordIndex]);
    },
    [table.records, table.updateRecord]
  );

  const parameterColumns: TableColumn[] = useMemo(() => {
    const data = parameterTemplates?.data || [];

    return data.map((template: any) => {
      let title = template.name;

      if (template.units) {
        title += ` [${template.units}]`;
      }

      const filters = parameterFilters[`parameter_${template.pk}`] || {};

      return {
        accessor: `parameter_${template.pk}`,
        title: title,
        sortable: true,
        extra: {
          template: template.pk
        },
        render: (record: any) => (
          <ParameterCell
            record={record}
            template={template}
            canEdit={user.hasChangeRole(UserRoles.part)}
          />
        ),
        filtering: Object.keys(filters).length > 0,
        filter: ({ close }: { close: () => void }) => {
          return (
            <ParameterFilter
              template={template}
              filters={parameterFilters[`parameter_${template.pk}`] || {}}
              setFilter={addParameterFilter}
              clearFilter={clearParameterFilter}
              closeFilter={close}
            />
          );
        }
      };
    });
  }, [user, parameterTemplates.data, parameterFilters]);

  // Callback function when a parameter cell is clicked
  const onParameterClick = useCallback((template: number, instance: any) => {
    setSelectedTemplate(template);
    setSelectedInstance(instance.pk);
    const parameter = instance.parameters?.find(
      (p: any) => p.template == template
    );

    if (parameter) {
      setSelectedParameter(parameter.pk);
      editParameter.open();
    } else {
      addParameter.open();
    }
  }, []);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [...(customFilters || [])];
  }, [customFilters]);

  const tableColumns: TableColumn[] = useMemo(() => {
    return [...(customColumns || []), ...parameterColumns];
  }, [customColumns, parameterColumns]);

  const rowActions = useCallback(
    (record: any) => {
      return [
        {
          title: t`Add Parameter`,
          icon: <IconCirclePlus />,
          color: 'green',
          hidden: !user.hasAddPermission(modelType),
          onClick: () => {
            setSelectedInstance(record.pk);
            setSelectedTemplate(null);
            addParameter.open();
          }
        }
      ];
    },
    [modelType, user]
  );

  return (
    <>
      {addParameter.modal}
      {editParameter.modal}
      <InvenTreeTable
        url={apiUrl(endpoint)}
        tableState={table}
        columns={tableColumns}
        props={{
          enableDownload: true,
          rowActions: rowActions,
          tableFilters: tableFilters,
          params: {
            ...queryParams,
            parameters: true,
            ...parametricQueryFilters
          },
          modelType: modelType,
          onCellClick: ({ event, record, index, column, columnIndex }) => {
            cancelEvent(event);

            // Is this a "parameter" cell?
            if (column?.accessor?.toString()?.startsWith('parameter_')) {
              const col = column as any;
              onParameterClick(col.extra.template, record);
            } else if (record?.pk) {
              // Navigate through to the detail page
              const url = getDetailUrl(modelType, record.pk);
              navigateToLink(url, navigate, event);
            }
          }
        }}
      />
    </>
  );
}
