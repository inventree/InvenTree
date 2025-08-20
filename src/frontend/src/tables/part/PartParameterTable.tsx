import { t } from '@lingui/core/macro';
import { Alert, Stack, Text } from '@mantine/core';
import { IconLock } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '@lib/components/AddItemButton';
import {
  type RowAction,
  RowDeleteAction,
  RowEditAction
} from '@lib/components/RowActions';
import { YesNoButton } from '@lib/components/YesNoButton';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { TableFilter } from '@lib/types/Filters';
import type { ApiFormFieldSet } from '@lib/types/Forms';
import type { TableColumn } from '@lib/types/Tables';
import { RenderUser } from '../../components/render/User';
import { formatDecimal } from '../../defaults/formatters';
import { usePartParameterFields } from '../../forms/PartForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import {
  DateColumn,
  DescriptionColumn,
  NoteColumn,
  PartColumn
} from '../ColumnRenderers';
import { IncludeVariantsFilter, UserFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { TableHoverCard } from '../TableHoverCard';

/**
 * Construct a table listing parameters for a given part
 */
export function PartParameterTable({
  partId,
  partLocked
}: Readonly<{
  partId: any;
  partLocked?: boolean;
}>) {
  const table = useTable('part-parameters');

  const user = useUserState();

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      PartColumn({
        part: 'part_detail'
      }),
      {
        accessor: 'part_detail.IPN',
        sortable: false,
        switchable: true,
        defaultVisible: false
      },
      {
        accessor: 'template_detail.name',
        switchable: false,
        sortable: true,
        ordering: 'name',
        render: (record) => {
          const variant = String(partId) != String(record.part);

          return (
            <Text style={{ fontStyle: variant ? 'italic' : 'inherit' }}>
              {record.template_detail?.name}
            </Text>
          );
        }
      },
      DescriptionColumn({
        accessor: 'template_detail.description'
      }),
      {
        accessor: 'data',
        switchable: false,
        sortable: true,
        render: (record) => {
          const template = record.template_detail;

          if (template?.checkbox) {
            return <YesNoButton value={record.data} />;
          }

          const extra: any[] = [];

          if (
            template.units &&
            record.data_numeric &&
            record.data_numeric != record.data
          ) {
            const numeric = formatDecimal(record.data_numeric, { digits: 15 });
            extra.push(`${numeric} [${template.units}]`);
          }

          return (
            <TableHoverCard
              value={record.data}
              extra={extra}
              title={t`Internal Units`}
            />
          );
        }
      },
      {
        accessor: 'template_detail.units',
        ordering: 'units',
        sortable: true
      },
      NoteColumn({}),
      DateColumn({
        accessor: 'updated',
        title: t`Last Updated`,
        sortable: true,
        switchable: true
      }),
      {
        accessor: 'updated_by',
        title: t`Updated By`,
        sortable: true,
        switchable: true,
        render: (record: any) => {
          return record.updated_by_detail ? (
            <RenderUser instance={record.updated_by_detail} />
          ) : (
            '-'
          );
        }
      }
    ];
  }, [partId]);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      IncludeVariantsFilter(),
      UserFilter({
        name: 'updated_by',
        label: t`Updated By`,
        description: t`Filter by user who last updated the parameter`
      })
    ];
  }, []);

  const partParameterFields: ApiFormFieldSet = usePartParameterFields({});

  const newParameter = useCreateApiFormModal({
    url: ApiEndpoints.part_parameter_list,
    title: t`New Part Parameter`,
    fields: useMemo(() => ({ ...partParameterFields }), [partParameterFields]),
    focus: 'template',
    initialData: {
      part: partId
    },
    table: table
  });

  const [selectedParameter, setSelectedParameter] = useState<
    number | undefined
  >(undefined);

  const editParameter = useEditApiFormModal({
    url: ApiEndpoints.part_parameter_list,
    pk: selectedParameter,
    title: t`Edit Part Parameter`,
    focus: 'data',
    fields: useMemo(() => ({ ...partParameterFields }), [partParameterFields]),
    table: table
  });

  const deleteParameter = useDeleteApiFormModal({
    url: ApiEndpoints.part_parameter_list,
    pk: selectedParameter,
    title: t`Delete Part Parameter`,
    table: table
  });

  // Callback for row actions
  const rowActions = useCallback(
    (record: any): RowAction[] => {
      // Actions not allowed for "variant" rows
      if (String(partId) != String(record.part)) {
        return [];
      }

      return [
        RowEditAction({
          tooltip: t`Edit Part Parameter`,
          hidden: partLocked || !user.hasChangeRole(UserRoles.part),
          onClick: () => {
            setSelectedParameter(record.pk);
            editParameter.open();
          }
        }),
        RowDeleteAction({
          tooltip: t`Delete Part Parameter`,
          hidden: partLocked || !user.hasDeleteRole(UserRoles.part),
          onClick: () => {
            setSelectedParameter(record.pk);
            deleteParameter.open();
          }
        })
      ];
    },
    [partId, partLocked, user]
  );

  // Custom table actions
  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add-parameter'
        hidden={partLocked || !user.hasAddRole(UserRoles.part)}
        tooltip={t`Add parameter`}
        onClick={() => newParameter.open()}
      />
    ];
  }, [partLocked, user]);

  return (
    <>
      {newParameter.modal}
      {editParameter.modal}
      {deleteParameter.modal}
      <Stack gap='xs'>
        {partLocked && (
          <Alert
            title={t`Part is Locked`}
            color='orange'
            icon={<IconLock />}
            p='xs'
          >
            <Text>{t`Part parameters cannot be edited, as the part is locked`}</Text>
          </Alert>
        )}
        <InvenTreeTable
          url={apiUrl(ApiEndpoints.part_parameter_list)}
          tableState={table}
          columns={tableColumns}
          props={{
            rowActions: rowActions,
            enableDownload: true,
            tableActions: tableActions,
            tableFilters: tableFilters,
            params: {
              part: partId,
              template_detail: true,
              part_detail: true
            }
          }}
        />
      </Stack>
    </>
  );
}
