import { ApiEndpoints, apiUrl } from '@lib/index';
import { t } from '@lingui/core/macro';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import type { TableColumn } from '../Column';
import {
  CategoryColumn,
  DescriptionColumn,
  PartColumn
} from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

export function PartTestTable({
  partId,
  categoryId
}: Readonly<{
  partId?: number;
  categoryId?: number;
}>) {
  const table = useTable('part-test');
  const user = useUserState();
  const navigate = useNavigate();

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'part',
        title: t`Part`,
        render: (record: any) => <PartColumn part={record.part_detail} />
      },
      CategoryColumn({
        accessor: 'category_detail'
      }),
      {
        accessor: 'template_detail.test_name',
        title: t`Template`,
        switchable: false
      },
      DescriptionColumn({
        accessor: 'template_detail.description'
      })
    ];
  }, []);

  // TODO: Table filters

  // TODO: Table actions

  // TODO: Row actions

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.part_test_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        params: {
          part: partId,
          category: categoryId
        }
      }}
    />
  );
}
