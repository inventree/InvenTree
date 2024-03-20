import { t } from '@lingui/macro';
import { ActionIcon, Group, Text, Tooltip } from '@mantine/core';
import { useHover } from '@mantine/hooks';
import { IconEdit } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { api } from '../../App';
import { ApiFormFieldSet } from '../../components/forms/fields/ApiFormField';
import { YesNoButton } from '../../components/items/YesNoButton';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { getDetailUrl } from '../../functions/urls';
import {
  useCreateApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { DescriptionColumn, PartColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import { TableHoverCard } from '../TableHoverCard';

// Render an individual parameter cell
function ParameterCell({
  record,
  template,
  canEdit,
  onEdit
}: {
  record: any;
  template: any;
  canEdit: boolean;
  onEdit: () => void;
}) {
  const { hovered, ref } = useHover();

  // Find matching template parameter
  let parameter = record.parameters?.find(
    (p: any) => p.template == template.pk
  );

  let extra: any[] = [];

  let value: any = parameter?.data;

  if (template?.checkbox && value != undefined) {
    value = <YesNoButton value={parameter.data} />;
  }

  if (
    template.units &&
    parameter &&
    parameter.data_numeric &&
    parameter.data_numeric != parameter.data
  ) {
    extra.push(`${parameter.data_numeric} [${template.units}]`);
  }

  const handleClick = useCallback((event: any) => {
    event?.preventDefault();
    event?.stopPropagation();
    event?.nativeEvent?.stopImmediatePropagation();
    onEdit();
  }, []);

  return (
    <div>
      <Group grow ref={ref} position="apart">
        <Group grow style={{ flex: 1 }}>
          <TableHoverCard
            value={value ?? '-'}
            extra={extra}
            title={t`Internal Units`}
          />
        </Group>
        {hovered && canEdit && (
          <div style={{ flex: 0 }}>
            <Tooltip label={t`Edit parameter`}>
              <ActionIcon size="xs" onClick={handleClick}>
                <IconEdit />
              </ActionIcon>
            </Tooltip>
          </div>
        )}
      </Group>
    </div>
  );
}

export default function ParametricPartTable({
  categoryId
}: {
  categoryId?: any;
}) {
  const table = useTable('parametric-parts');
  const user = useUserState();
  const navigate = useNavigate();

  const categoryParmeters = useQuery({
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

  const partParameterFields: ApiFormFieldSet = useMemo(() => {
    return {
      part: {
        disabled: true
      },
      template: {
        disabled: true
      },
      data: {}
    };
  }, []);

  const addParameter = useCreateApiFormModal({
    url: ApiEndpoints.part_parameter_list,
    title: t`Add Part Parameter`,
    fields: partParameterFields,
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
    fields: partParameterFields,
    onFormSuccess: (parameter: any) => {
      updateParameterRecord(selectedPart, parameter);
    }
  });

  // Update a single parameter record in the table
  const updateParameterRecord = useCallback((part: number, parameter: any) => {
    let records = table.records;
    let partIndex = records.findIndex((record: any) => record.pk == part);

    if (partIndex < 0) {
      // No matching part: reload the entire table
      table.refreshTable();
      return;
    }

    let parameterIndex = records[partIndex].parameters.findIndex(
      (p: any) => p.pk == parameter.pk
    );

    if (parameterIndex < 0) {
      // No matching parameter - append new parameter
      records[partIndex].parameters.push(parameter);
    } else {
      records[partIndex].parameters[parameterIndex] = parameter;
    }

    table.setRecords(records);
  }, []);

  const parameterColumns: TableColumn[] = useMemo(() => {
    let data = categoryParmeters.data ?? [];

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
            onEdit={() => {
              setSelectedTemplate(template.pk);
              setSelectedPart(record.pk);
              let parameter = record.parameters?.find(
                (p: any) => p.template == template.pk
              );

              if (parameter) {
                setSelectedParameter(parameter.pk);
                editParameter.open();
              } else {
                addParameter.open();
              }
            }}
          />
        )
      };
    });
  }, [user, categoryParmeters.data]);

  const tableColumns: TableColumn[] = useMemo(() => {
    const partColumns: TableColumn[] = [
      {
        accessor: 'name',
        sortable: true,
        switchable: false,
        noWrap: true,
        render: (record: any) => PartColumn(record)
      },
      DescriptionColumn({}),
      {
        accessor: 'IPN',
        sortable: true
      }
    ];

    return [...partColumns, ...parameterColumns];
  }, [parameterColumns]);

  // Callback when a parameter cell is clicked - either edit or add a new parameter
  const handleCellClick = useCallback(
    (record: any, column: any) => {
      let template_id = column?.extra?.template;

      if (!template_id) {
        return;
      }

      setSelectedPart(record.pk);
      setSelectedTemplate(template_id);

      // Find the associated parameter
      let parameter = record?.parameters?.find(
        (p: any) => p.template == template_id
      );

      if (parameter) {
        // Parameter exists - open edit dialog
        setSelectedParameter(parameter.pk);
        editParameter.open();
      } else {
        // Parameter does not exist - create it!
        addParameter.open();
      }
    },
    [user]
  );

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
          params: {
            category: categoryId,
            cascade: true,
            category_detail: true,
            parameters: true
          },
          onRowClick: (record) => {
            if (record.pk) {
              navigate(getDetailUrl(ModelType.part, record.pk));
            }
          }
        }}
      />
    </>
  );
}
