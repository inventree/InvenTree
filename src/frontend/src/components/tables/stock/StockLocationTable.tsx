import { t } from '@lingui/macro';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { ApiPaths } from '../../../enums/ApiEndpoints';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { YesNoButton } from '../../items/YesNoButton';
import { TableColumn } from '../Column';
import { DescriptionColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

/**
 * Stock location table
 */
export function StockLocationTable({ params = {} }: { params?: any }) {
  const table = useTable('stocklocation');

  const navigate = useNavigate();

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        title: t`Name`,
        switchable: false
      },
      DescriptionColumn(),
      {
        accessor: 'pathstring',
        title: t`Path`,
        sortable: true
      },
      {
        accessor: 'items',
        title: t`Stock Items`,

        sortable: true
      },
      {
        accessor: 'structural',
        title: t`Structural`,

        sortable: true,
        render: (record: any) => <YesNoButton value={record.structural} />
      },
      {
        accessor: 'external',
        title: t`External`,

        sortable: true,
        render: (record: any) => <YesNoButton value={record.external} />
      },
      {
        accessor: 'location_type',
        title: t`Location Type`,

        sortable: false,
        render: (record: any) => record.location_type_detail?.name
      }
    ];
  }, [params]);

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.stock_location_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        enableDownload: true,
        params: params,
        onRowClick: (record) => {
          navigate(`/stock/location/${record.pk}`);
        }
        // TODO: allow for "tree view" with cascade
      }}
    />
  );
}
