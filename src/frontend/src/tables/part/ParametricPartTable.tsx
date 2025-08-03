import { t } from '@lingui/core/macro';
import { Group } from '@mantine/core';
import { useHover } from '@mantine/hooks';
import { useQuery } from '@tanstack/react-query';
import { type ReactNode, useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { YesNoButton } from '@lib/components/YesNoButton';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import { cancelEvent } from '@lib/functions/Events';
import { getDetailUrl } from '@lib/functions/Navigation';
import { navigateToLink } from '@lib/functions/Navigation';
import type { TableFilter } from '@lib/types/Filters';
import type { ApiFormFieldSet } from '@lib/types/Forms';
import type { TableColumn } from '@lib/types/Tables';
import { useApi } from '../../contexts/ApiContext';
import { formatDecimal } from '../../defaults/formatters';
import { usePartParameterFields } from '../../forms/PartForms';
import {
  useCreateApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import { DescriptionColumn, PartColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import { TableHoverCard } from '../TableHoverCard';
import {
  PARAMETER_FILTER_OPERATORS,
  ParameterFilter
} from './ParametricPartTableFilters';

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
  }, [record.parameters, template]);

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

export default function ParametricPartTable({
  categoryId
}: Readonly<{
  categoryId?: any;
}>) {
  const api = useApi();
  const table = useTable('parametric-parts');
  const user = useUserState();
  const navigate = useNavigate();

  const categoryParameters = useQuery({
    queryKey: ['category-parameters', categoryId],
    queryFn: async () => {
      return api
        .get(apiUrl(ApiEndpoints.part_parameter_template_list), {
          params: {
            category: categoryId
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

        if (paramFilters[operator]) {
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

      setParameterFilters((prev: any) => {
        const filters = { ...prev };
        const paramFilters = filters[filterName] || {};

        paramFilters[operator] = value;

        return {
          ...filters,
          [filterName]: paramFilters
        };
      });

      table.refreshTable();
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

  const [selectedPart, setSelectedPart] = useState<number>(0);
  const [selectedTemplate, setSelectedTemplate] = useState<number>(0);
  const [selectedParameter, setSelectedParameter] = useState<number>(0);

  const partParameterFields: ApiFormFieldSet = usePartParameterFields({
    editTemplate: false
  });

  const addParameter = useCreateApiFormModal({
    url: ApiEndpoints.part_parameter_list,
    title: t`Add Part Parameter`,
    fields: useMemo(() => ({ ...partParameterFields }), [partParameterFields]),
    focus: 'data',
    onFormSuccess: (parameter: any) => {
      updateParameterRecord(selectedPart, parameter);
    },
    initialData: {
      part: selectedPart,
      template: selectedTemplate
    }
  });

  const editParameter = useEditApiFormModal({
    url: ApiEndpoints.part_parameter_list,
    title: t`Edit Part Parameter`,
    pk: selectedParameter,
    fields: useMemo(() => ({ ...partParameterFields }), [partParameterFields]),
    focus: 'data',
    onFormSuccess: (parameter: any) => {
      updateParameterRecord(selectedPart, parameter);
    }
  });

  // Update a single parameter record in the table
  const updateParameterRecord = useCallback(
    (part: number, parameter: any) => {
      const records = table.records;
      const partIndex = records.findIndex((record: any) => record.pk == part);

      if (partIndex < 0) {
        // No matching part: reload the entire table
        table.refreshTable();
        return;
      }

      const parameterIndex = records[partIndex].parameters.findIndex(
        (p: any) => p.pk == parameter.pk
      );

      if (parameterIndex < 0) {
        // No matching parameter - append new parameter
        records[partIndex].parameters.push(parameter);
      } else {
        records[partIndex].parameters[parameterIndex] = parameter;
      }

      table.updateRecord(records[partIndex]);
    },
    [table.updateRecord]
  );

  const parameterColumns: TableColumn[] = useMemo(() => {
    const data = categoryParameters?.data || [];

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
  }, [user, categoryParameters.data, parameterFilters]);

  const onParameterClick = useCallback((template: number, part: any) => {
    setSelectedTemplate(template);
    setSelectedPart(part.pk);
    const parameter = part.parameters?.find((p: any) => p.template == template);

    if (parameter) {
      setSelectedParameter(parameter.pk);
      editParameter.open();
    } else {
      addParameter.open();
    }
  }, []);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'active',
        label: t`Active`,
        description: t`Show active parts`
      },
      {
        name: 'locked',
        label: t`Locked`,
        description: t`Show locked parts`
      },
      {
        name: 'assembly',
        label: t`Assembly`,
        description: t`Show assembly parts`
      }
    ];
  }, []);

  const tableColumns: TableColumn[] = useMemo(() => {
    const partColumns: TableColumn[] = [
      {
        accessor: 'name',
        title: t`Part`,
        sortable: true,
        switchable: false,
        noWrap: true,
        render: (record: any) => PartColumn({ part: record })
      },
      DescriptionColumn({
        defaultVisible: false
      }),
      {
        accessor: 'IPN',
        sortable: true,
        defaultVisible: false
      },
      {
        accessor: 'total_in_stock',
        sortable: true
      }
    ];

    return [...partColumns, ...parameterColumns];
  }, [parameterColumns]);

  return (
    <>
      {addParameter.modal}
      {editParameter.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.part_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          enableDownload: true,
          tableFilters: tableFilters,
          params: {
            category: categoryId,
            cascade: true,
            category_detail: true,
            parameters: true,
            ...parametricQueryFilters
          },
          onCellClick: ({ event, record, index, column, columnIndex }) => {
            cancelEvent(event);

            // Is this a "parameter" cell?
            if (column?.accessor?.toString()?.startsWith('parameter_')) {
              const col = column as any;
              onParameterClick(col.extra.template, record);
            } else if (record?.pk) {
              // Navigate through to the part detail page
              const url = getDetailUrl(ModelType.part, record.pk);
              navigateToLink(url, navigate, event);
            }
          }
        }}
      />
    </>
  );
}
