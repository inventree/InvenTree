import { t } from '@lingui/macro';
import { Group, Text } from '@mantine/core';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { ApiPaths } from '../../../enums/ApiEndpoints';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { Thumbnail } from '../../images/Thumbnail';
import { DescriptionColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

/**
 * A table which displays a list of company records,
 * based on the provided filter parameters
 */
export function CompanyTable({
  params,
  path
}: {
  params?: any;
  path?: string;
}) {
  const table = useTable('company');

  const navigate = useNavigate();

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
                src={record.thumbnail ?? record.image ?? ''}
                alt={record.name}
                size={24}
              />
              <Text>{record.name}</Text>
            </Group>
          );
        }
      },
      DescriptionColumn(),
      {
        accessor: 'website',
        title: t`Website`,
        sortable: false
      }
    ];
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.company_list)}
      tableState={table}
      columns={columns}
      props={{
        params: {
          ...params
        },
        onRowClick: (row: any) => {
          if (row.pk) {
            let base = path ?? 'company';
            navigate(`/${base}/${row.pk}`);
          }
        }
      }}
    />
  );
}
