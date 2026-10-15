import { t } from '@lingui/core/macro';
import { Alert, Group, Stack, Text } from '@mantine/core';
import { IconLock } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AddItemButton } from '@lib/components/AddItemButton';
import {
  type RowAction,
  RowDeleteAction,
  RowEditAction
} from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import useTable from '@lib/hooks/UseTable';
import type { TableFilter } from '@lib/types/Filters';
import type { ApiFormFieldSet } from '@lib/types/Forms';
import type { TableColumn } from '@lib/types/Tables';
import { AppRowViewAction } from '../../components/tables/AppRowActions';
import {
  BooleanColumn,
  DescriptionColumn,
  PartColumn
} from '../../components/tables/ColumnRenderers';
import { InvenTreeTable } from '../../components/tables/InvenTreeTable';
import { TableHoverCard } from '../../components/tables/TableHoverCard';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useUserState } from '../../states/UserState';

export function PartTestTable({
  partId,
  partLocked
}: Readonly<{
  partId?: number;
  partLocked?: boolean;
}>) {
  const user = useUserState();
  const navigate = useNavigate();
  const table = useTable('part-test');
  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      PartColumn({
        accessor: 'part_detail',
        switchable: true
      }),
      {
        accessor: 'template_detail.test_name',
        title: t`Test Template`,
        switchable: false,
        render: (record: any) => {
          const extra: string[] = [];

          if (record.part && partId && record.part != partId) {
            extra.push(t`Test defined for a higher level part`);
          }

          return (
            <Group gap='xs' wrap='nowrap' justify='space-between'>
              {record.template_detail.test_name}
              {extra.length > 0 && (
                <TableHoverCard
                  value=''
                  position='bottom-end'
                  icon='info'
                  title={t`Details`}
                  extra={extra}
                />
              )}
            </Group>
          );
        }
      },
      DescriptionColumn({
        accessor: 'template_detail.description',
        switchable: true
      }),
      BooleanColumn({
        accessor: 'enabled',
        title: t`Enabled`,
        switchable: true,
        sortable: true
      }),
      BooleanColumn({
        accessor: 'required',
        title: t`Required`,
        switchable: true,
        sortable: true
      }),
      BooleanColumn({
        accessor: 'template_detail.requires_value',
        title: t`Requires Value`,
        switchable: true,
        sortable: false,
        defaultVisible: false
      }),
      BooleanColumn({
        accessor: 'template_detail.requires_attachment',
        title: t`Requires Attachment`,
        switchable: true,
        sortable: false,
        defaultVisible: false
      })
    ];
  }, [partId]);

  const partTestFields: ApiFormFieldSet = useMemo(() => {
    return {
      part: {},
      template: {},
      enabled: {},
      required: {}
    };
  }, []);

  const [selectedTestId, setSelectedTestId] = useState<number | undefined>(
    undefined
  );

  const newTest = useCreateApiFormModal({
    url: ApiEndpoints.part_test_list,
    title: t`Add Test`,
    fields: useMemo(() => ({ ...partTestFields }), [partTestFields]),
    initialData: {
      part: partId
    },
    focus: 'template',
    table: table
  });

  const editTest = useEditApiFormModal({
    url: ApiEndpoints.part_test_list,
    pk: selectedTestId,
    title: t`Edit Test`,
    fields: useMemo(() => ({ ...partTestFields }), [partTestFields]),
    focus: 'template',
    table: table
  });

  const deleteTest = useDeleteApiFormModal({
    url: ApiEndpoints.part_test_list,
    pk: selectedTestId,
    title: t`Delete Test`,
    table: table
  });

  // Table filters
  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'enabled',
        label: t`Enabled`,
        description: t`Show enabled tests`
      },
      {
        name: 'required',
        label: t`Required`,
        description: t`Show required tests`
      },
      {
        name: 'include_inherited',
        label: t`Include Inherited`,
        description: t`Show tests from inherited templates`
      }
    ];
  }, []);

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add-test'
        tooltip={t`Add Test`}
        hidden={partLocked || !user.hasAddPermission(ModelType.parttest)}
        onClick={() => {
          newTest.open();
        }}
      />
    ];
  }, [user, partLocked]);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      // This test is defined for a different part
      if (partId && record.part && record.part != partId) {
        return [
          AppRowViewAction({
            title: t`View Part`,
            modelType: ModelType.part,
            modelId: record.part,
            navigate: navigate
          })
        ];
      }
      return [
        RowEditAction({
          hidden: partLocked || !user.hasChangePermission(ModelType.parttest),
          onClick: () => {
            setSelectedTestId(record.pk);
            editTest.open();
          }
        }),
        RowDeleteAction({
          hidden: partLocked || !user.hasDeletePermission(ModelType.parttest),
          onClick: () => {
            setSelectedTestId(record.pk);
            deleteTest.open();
          }
        })
      ];
    },
    [partId, partLocked, navigate, user]
  );

  return (
    <>
      {newTest.modal}
      {editTest.modal}
      {deleteTest.modal}
      <Stack gap='xs'>
        {partLocked && (
          <Alert
            title={t`Part is Locked`}
            color='orange'
            icon={<IconLock />}
            p='xs'
          >
            <Text>{t`Part tests cannot be edited, as the part is locked`}</Text>
          </Alert>
        )}
        <InvenTreeTable
          url={apiUrl(ApiEndpoints.part_test_list)}
          tableState={table}
          columns={tableColumns}
          props={{
            params: {
              for_part: partId
            },
            rowActions: rowActions,
            tableFilters: tableFilters,
            tableActions: tableActions
          }}
        />
      </Stack>
    </>
  );
}
