import { t } from '@lingui/macro';
import { Group, Text } from '@mantine/core';
import { useMemo } from 'react';

import { useTableRefresh } from '../../../hooks/TableRefresh';
import { ApiPaths, apiUrl } from '../../../states/ApiState';
import { Thumbnail } from '../../images/Thumbnail';
import { InvenTreeTable } from '../InvenTreeTable';

/**
 * A table which displays a list of company records,
 * based on the provided filter parameters
 */
export function CompanyTable({ params }: { params?: any }) {
  const { tableKey } = useTableRefresh('company');

  const columns = useMemo(() => {
    return [
      {
        accessor: 'name',
        title: t`Company Name`,
        sortable: true,
        render: (record: any) => {
          return (
            <Group spacing="xs" noWrap={true}>
              <Thumbnail
                src={record.thumbnail ?? record.image}
                alt={record.name}
                size={24}
              />
              <Text>{record.name}</Text>
            </Group>
          );
        }
      },
      {
        accessor: 'description',
        title: t`Description`,
        sortable: false,
        switchable: true
      },
      {
        accessor: 'website',
        title: t`Website`,
        sortable: false,
        switchable: true
      }
    ];
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.company_list)}
      tableKey={tableKey}
      columns={columns}
      props={{
        params: {
          ...params
        }
      }}
    />
  );
}
