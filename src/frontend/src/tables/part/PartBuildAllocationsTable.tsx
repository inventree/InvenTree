import { t } from '@lingui/macro';
import { useMemo } from 'react';

import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { TableColumn } from '../Column';
import {
  LocationColumn,
  ReferenceColumn,
  StatusColumn
} from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

export default function PartBuildAlloctionsTable({
  partId
}: {
  partId: number;
}) {
  const table = useTable('partbuildallocations');

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      ReferenceColumn({
        accessor: 'build_detail.reference',
        title: t`Build Order`,
        switchable: false
      }),
      {
        accessor: 'build_detail.title',
        title: t`Description`
      },
      StatusColumn({
        accessor: 'build_detail.status',
        model: ModelType.build
      }),
      {
        accessor: 'quantity',
        switchable: false,
        sortable: true
      },
      LocationColumn({
        accessor: 'location_detail'
      })
    ];
  }, []);

  return (
    <>
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.build_item_list)}
        columns={tableColumns}
        tableState={table}
        props={{
          params: {
            part: partId,
            build_detail: true,
            location_detail: true,
            stock_detail: true
          },
          modelField: 'build',
          modelType: ModelType.build
        }}
      />
    </>
  );
}
