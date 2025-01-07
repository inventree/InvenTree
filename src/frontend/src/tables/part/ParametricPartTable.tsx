import { t } from '@lingui/macro';
import { Group } from '@mantine/core';
import { useHover } from '@mantine/hooks';
import { useQuery } from '@tanstack/react-query';
import { type ReactNode, useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { YesNoButton } from '../../components/buttons/YesNoButton';
import type { ApiFormFieldSet } from '../../components/forms/fields/ApiFormField';
import { useApi } from '../../contexts/ApiContext';
import { formatDecimal } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { usePartParameterFields } from '../../forms/PartForms';
import { cancelEvent } from '../../functions/events';
import { navigateToLink } from '../../functions/navigation';
import { getDetailUrl } from '../../functions/urls';
import {
  useCreateApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import type { TableColumn } from '../Column';
import { DescriptionColumn, PartColumn } from '../ColumnRenderers';
import type { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { TableHoverCard } from '../TableHoverCard';

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
        .then((response) => response.data)
        .catch((_error) => []);
    },
    refetchOnMount: true
  });

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
    const data = categoryParameters.data ?? [];

    return data.map((template: any) => {
      let title = template.name;

      if (template.units) {
        title += ` [${template.units}]`;
      }

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
        )
      };
    });
  }, [user, categoryParameters.data]);

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
        sortable: true,
        switchable: false,
        noWrap: true,
        render: (record: any) => PartColumn({ part: record })
      },
      DescriptionColumn({}),
      {
        accessor: 'IPN',
        sortable: true
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
          enableDownload: false,
          tableFilters: tableFilters,
          params: {
            category: categoryId,
            cascade: true,
            category_detail: true,
            parameters: true
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
