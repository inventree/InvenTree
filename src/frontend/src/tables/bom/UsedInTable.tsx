import { t } from '@lingui/core/macro';
import { Group, Text } from '@mantine/core';
import { useMemo } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import type { TableFilter } from '@lib/types/Filters';
import { formatDecimal } from '../../defaults/formatters';
import { useTable } from '../../hooks/UseTable';
import type { TableColumn } from '../Column';
import { PartColumn, ReferenceColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

/*
 * For a given part, render a table showing all the assemblies the part is used in
 */
export function UsedInTable({
  partId,
  params = {}
}: Readonly<{
  partId: number;
  params?: any;
}>) {
  const table = useTable('usedin');

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'part',
        switchable: false,
        sortable: true,
        title: t`Assembly`,
        render: (record: any) => PartColumn({ part: record.part_detail })
      },
      {
        accessor: 'part_detail.IPN',
        sortable: false,
        title: t`IPN`
      },
      {
        accessor: 'part_detail.revision',
        title: t`Revision`,
        sortable: true
      },
      {
        accessor: 'part_detail.description',
        sortable: false,
        title: t`Description`
      },
      {
        accessor: 'sub_part',
        sortable: true,
        title: t`Component`,
        render: (record: any) => PartColumn({ part: record.sub_part_detail })
      },
      {
        accessor: 'quantity',
        switchable: false,
        render: (record: any) => {
          const quantity = formatDecimal(record.quantity);
          const units = record.sub_part_detail?.units;

          return (
            <Group justify='space-between' grow wrap='nowrap'>
              <Text>{quantity}</Text>
              {units && <Text size='xs'>{units}</Text>}
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
