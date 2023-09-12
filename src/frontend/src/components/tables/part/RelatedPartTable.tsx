import { t } from '@lingui/macro';
import { Group, Text } from '@mantine/core';
import { ReactNode, useCallback, useMemo } from 'react';

import { notYetImplemented } from '../../../functions/notifications';
import { Thumbnail } from '../../items/Thumbnail';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';

export function RelatedPartTable({ partId }: { partId: number }): ReactNode {
  const tableColumns: TableColumn[] = useMemo(() => {
    function getPart(record: any) {
      if (record.part_1 == partId) {
        return record.part_2_detail;
      } else {
        return record.part_1_detail;
      }
    }

    return [
      {
        accessor: 'part',
        title: t`Part`,
        render: (record: any) => {
          let part = getPart(record);
          return (
            <Group>
              <Thumbnail image={part.thumbnail || part.image} />
              <Text>{part.name}</Text>
            </Group>
          );
        }
      },
      {
        accessor: 'description',
        title: t`Description`,
        render: (record: any) => {
          return getPart(record).description;
        }
      }
    ];
  }, []);

  // Generate row actions
  // TODO: Hide if user does not have permission to edit parts
  const rowActions = useCallback((record: any) => {
    return [
      {
        title: t`Delete`,
        color: 'red',
        onClick: () => {
          // TODO
          notYetImplemented();
        }
      }
    ];
  }, []);

  return (
    <InvenTreeTable
      url="/part/related/"
      tableKey="related-part-table"
      params={{
        part: partId
      }}
      rowActions={rowActions}
      columns={tableColumns}
    />
  );
}
