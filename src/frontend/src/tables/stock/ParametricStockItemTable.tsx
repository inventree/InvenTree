import { ApiEndpoints, ModelType } from '@lib/index';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { t } from '@lingui/core/macro';
import { useMemo } from 'react';
import {
  DescriptionColumn,
  IPNColumn,
  PartColumn,
  StockColumn
} from '../ColumnRenderers';
import ParametricDataTable from '../general/ParametricDataTable';

export default function ParametricStockItemTable({
  locationId
}: Readonly<{
  locationId?: any;
}>) {
  const customFilters: TableFilter[] = useMemo(() => {
    // Custom filters for the parametric stock item table
    return [];
  }, []);

  const customColumns: TableColumn[] = useMemo(() => {
    return [
      PartColumn({
        part: 'part_detail',
        switchable: false
      }),
      IPNColumn({}),
      DescriptionColumn({
        accessor: 'part_detail.description'
      }),
      StockColumn({
        accessor: '',
        title: t`Stock`,
        sortable: true,
        ordering: 'stock'
      })
    ];
  }, []);

  return (
    <ParametricDataTable
      modelType={ModelType.stockitem}
      relatedModel={'location'}
      relatedModelId={locationId}
      endpoint={ApiEndpoints.stock_item_list}
      customColumns={customColumns}
      customFilters={customFilters}
      queryParams={{
        location: locationId,
        cascade: true,
        location_detail: true,
        part_detail: true
      }}
    />
  );
}
