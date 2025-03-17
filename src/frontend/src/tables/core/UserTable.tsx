import type { TableFilter } from '@lib/components/tables/Filter';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { t } from '@lingui/macro';
import { useMemo } from 'react';
import {} from '../../hooks/UseFilter';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { BooleanColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

export function UserTable() {
  const table = useTable('users-index');

  const tableFilters: TableFilter[] = useMemo(() => {
    const filters: TableFilter[] = [
      {
        name: 'is_active',
        label: t`Active`,
        description: t`Show active users`
      },
      {
        name: 'is_staff',
        label: t`Staff`,
        description: t`Show staff users`
      },
      {
        name: 'is_superuser',
        label: t`Superuser`,
        description: t`Show superusers`
      }
    ];

    return filters;
  }, []);

  const tableColumns = useMemo(() => {
    return [
      {
        accessor: 'username',
        sortable: true,
        switchable: false
      },
      {
        accessor: 'first_name',
        sortable: true
      },
      {
        accessor: 'last_name',
        sortable: true
      },
      {
        accessor: 'email',
        sortable: true
      },
      {
        accessor: 'groups',
        title: t`Groups`,
        sortable: true,
        switchable: true,
        render: (record: any) => {
          return record.groups.length;
        }
      },
      BooleanColumn({
        accessor: 'is_staff'
      }),
      BooleanColumn({
        accessor: 'is_superuser'
      }),
      BooleanColumn({
        accessor: 'is_active'
      })
    ];
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.user_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        tableFilters: tableFilters,
        modelType: ModelType.user
      }}
    />
  );
}
