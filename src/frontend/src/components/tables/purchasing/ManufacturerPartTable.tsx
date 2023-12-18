import { t } from '@lingui/macro';
import { ReactNode, useCallback, useMemo } from 'react';

import { ApiPaths } from '../../../enums/ApiEndpoints';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { useUserState } from '../../../states/UserState';
import { Thumbnail } from '../../images/Thumbnail';
import { RenderPart } from '../../render/Part';
import { TableColumn } from '../Column';
import { DescriptionColumn, LinkColumn, PartColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

/*
 * Construct a table listing manufacturer parts
 */
export function ManufacturerPartTable({ params }: { params: any }): ReactNode {
  const table = useTable('manufacturerparts');

  const user = useUserState();

  // Construct table columns for this table
  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'part',
        title: t`Part`,
        switchable: 'part' in params,
        sortable: true,
        render: (record: any) => RenderPart(record?.part_detail)
      },
      {
        accessor: 'manufacturer',
        title: t`Manufacturer`,
        sortable: true,
        render: (record: any) => {
          let manufacturer = record?.manufacturer_detail ?? {};

          return (
            <Thumbnail
              src={manufacturer?.thumbnail ?? manufacturer.image}
              text={manufacturer.name}
            />
          );
        }
      },
      {
        accessor: 'MPN',
        title: t`Manufacturer Part Number`,
        sortable: true
      },
      DescriptionColumn(),
      LinkColumn()
    ];
  }, [params]);

  const tableActions = useMemo(() => {
    // TODO: Custom actions
    return [];
  }, [user]);

  const rowActions = useCallback(
    (record: any) => {
      // TODO: Custom row actions
      return [];
    },
    [user]
  );

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.manufacturer_part_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        params: {
          ...params,
          part_detail: true,
          manufacturer_detail: true
        },
        rowActions: rowActions,
        customActionGroups: tableActions
      }}
    />
  );
}
