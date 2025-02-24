import { t } from '@lingui/macro';
import { useMemo } from 'react';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import {} from '../../hooks/UseFilter';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { BooleanColumn } from '../ColumnRenderers';
import type { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';

export function UserTable({
  userId,
  customerId
}: Readonly<{
  userId?: number;
  customerId?: number;
}>) {
  const table = useTable(!!userId ? 'users-part' : 'users-index');

  const tableFilters: TableFilter[] = useMemo(() => {
    const filters: TableFilter[] = [
      {
        name: 'has_target_date',
        type: 'boolean',
        label: t`Has Target Date`,
        description: t`Show orders with a target date`
      },
      {
        name: 'has_start_date',
        type: 'boolean',
        label: t`Has Start Date`,
        description: t`Show orders with a start date`
      }
    ];

    if (!!userId) {
      filters.push({
        name: 'include_variants',
        type: 'boolean',
        label: t`Include Variants`,
        description: t`Include orders for part variants`
      });
    }

    return filters;
  }, [userId]);

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
        params: {
          user: userId
        },
        tableFilters: tableFilters,
        modelType: ModelType.user,
        enableSelection: true,
        enableDownload: true
      }}
    />
  );
}
