import { t } from '@lingui/macro';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { PartHoverCard } from '../../components/images/Thumbnail';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { getDetailUrl } from '../../functions/urls';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { TableColumn } from '../Column';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';

/*
 * For a given part, render a table showing all the assemblies the part is used in
 */
export function UsedInTable({
  partId,
  params = {}
}: {
  partId: number;
  params?: any;
}) {
  const navigate = useNavigate();

  const table = useTable('usedin');

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'part',
        title: t`Assembled Part`,
        switchable: false,
        sortable: true,
        render: (record: any) => <PartHoverCard part={record.part_detail} />
      },
      {
        accessor: 'sub_part',
        title: t`Required Part`,
        sortable: true,
        render: (record: any) => <PartHoverCard part={record.sub_part_detail} />
      },
      {
        accessor: 'quantity',
        title: t`Quantity`,
        render: (record: any) => {
          // TODO: render units if appropriate
          return record.quantity;
        }
      },
      {
        accessor: 'reference',
        title: t`Reference`,
        sortable: true
      }
    ];
  }, [partId]);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'inherited',
        label: t`Gets Inherited`,
        description: t`Show inherited items`
      },
      {
        name: 'optional',
        label: t`Optional`,
        description: t`Show optional items`
      },
      {
        name: 'part_active',
        label: t`Active`,
        description: t`Show active assemblies`
      },
      {
        name: 'part_trackable',
        label: t`Trackable`,
        description: t`Show trackable assemblies`
      }
    ];
  }, [partId]);

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.bom_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        params: {
          ...params,
          uses: partId,
          part_detail: true,
          sub_part_detail: true
        },
        tableFilters: tableFilters,
        onRowClick: (row) => navigate(getDetailUrl(ModelType.part, row.part))
      }}
    />
  );
}
