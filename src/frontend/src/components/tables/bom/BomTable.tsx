import { t } from '@lingui/macro';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { useTableRefresh } from '../../../hooks/TableRefresh';
import { ApiPaths, apiUrl } from '../../../states/ApiState';
import { ThumbnailHoverCard } from '../../images/Thumbnail';
import { YesNoButton } from '../../items/YesNoButton';
import { TableColumn } from '../Column';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';

export function BomTable({
  partId,
  params = {}
}: {
  partId: number;
  params?: any;
}) {
  const navigate = useNavigate();

  const { tableKey, refreshTable } = useTableRefresh('bom');

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      // TODO: Improve column rendering
      {
        accessor: 'part',
        title: t`Part`,
        render: (row) => {
          let part = row.sub_part_detail;

          return (
            part && (
              <ThumbnailHoverCard
                src={part.thumbnail || part.image}
                text={part.full_name}
                alt={part.description}
                link=""
              />
            )
          );
        }
      },
      {
        accessor: 'description',
        title: t`Description`,
        render: (row) => row?.sub_part_detail?.description
      },
      {
        accessor: 'reference',
        title: t`Reference`
      },
      {
        accessor: 'quantity',
        title: t`Quantity`
      },
      {
        accessor: 'substitutes',
        title: t`Substitutes`
      },
      {
        accessor: 'optional',
        title: t`Optional`,
        switchable: true,
        sortable: true,
        render: (row) => {
          return <YesNoButton value={row.optional} />;
        }
      },
      {
        accessor: 'consumable',
        title: t`Consumable`,
        switchable: true,
        sortable: true,
        render: (row) => {
          return <YesNoButton value={row.consumable} />;
        }
      },
      {
        accessor: 'allow_variants',
        title: t`Allow Variants`,
        switchable: true,
        sortable: true,
        render: (row) => {
          return <YesNoButton value={row.allow_variants} />;
        }
      },
      {
        accessor: 'inherited',
        title: t`Gets Inherited`,
        switchable: true,
        sortable: true,
        render: (row) => {
          // TODO: Update complexity here
          return <YesNoButton value={row.inherited} />;
        }
      },
      {
        accessor: 'price_range',
        title: t`Price Range`
      },
      {
        accessor: 'available',
        title: t`Available`
      },
      {
        accessor: 'can_build',
        title: t`Can Build`
      },
      {
        accessor: 'notes',
        title: t`Notes`
      }
    ];
  }, [partId, params]);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [];
  }, [partId, params]);

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.bom_list)}
      tableKey={tableKey}
      columns={tableColumns}
      props={{
        params: {
          ...params,
          part: partId,
          part_detail: true,
          sub_part_detail: true
        },
        customFilters: tableFilters,
        onRowClick: (row) => navigate(`/part/${row.sub_part}`)
      }}
    />
  );
}
