import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { getDetailUrl } from '../../functions/urls';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { DescriptionColumn, PartColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

export default function ParametricPartTable({
  categoryId
}: {
  categoryId: any;
}) {
  const table = useTable('parametric-parts');
  const user = useUserState();
  const navigate = useNavigate();

  const tableColumns: TableColumn[] = useMemo(() => {
    const partColumns: TableColumn[] = [
      {
        accessor: 'name',
        sortable: true,
        noWrap: true,
        render: (record: any) => PartColumn(record)
      },
      DescriptionColumn({}),
      {
        accessor: 'IPN',
        sortable: true
      }
    ];

    return [...partColumns];
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.part_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        enableDownload: false,
        params: {
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
  );
}
