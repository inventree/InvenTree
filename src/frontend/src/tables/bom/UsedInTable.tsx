import { t } from '@lingui/macro';
import { Group, Text } from '@mantine/core';
import { useMemo } from 'react';

import { PartHoverCard } from '../../components/images/Thumbnail';
import { formatDecimal } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { TableColumn } from '../Column';
import { ReferenceColumn } from '../ColumnRenderers';
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
  const table = useTable('usedin');

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'part',
        switchable: false,
        sortable: true,
        render: (record: any) => <PartHoverCard part={record.part_detail} />
      },
      {
        accessor: 'sub_part',
        sortable: true,
        render: (record: any) => <PartHoverCard part={record.sub_part_detail} />
      },
      {
        accessor: 'quantity',
        render: (record: any) => {
          let quantity = formatDecimal(record.quantity);
          let units = record.sub_part_detail?.units;

          return (
            <Group justify="space-between" grow>
              <Text>{quantity}</Text>
              {units && <Text size="xs">{units}</Text>}
            </Group>
          );
        }
      },
      ReferenceColumn({})
    ];
  }, [partId]);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'inherited',
        label: t`Inherited`,
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
        modelType: ModelType.part,
        modelField: 'part'
      }}
    />
  );
}
