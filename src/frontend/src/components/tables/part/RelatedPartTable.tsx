import { t } from '@lingui/macro';
import { Group, Text } from '@mantine/core';
import { ReactNode, useCallback, useMemo } from 'react';

import { openDeleteApiForm } from '../../../functions/forms';
import { notYetImplemented } from '../../../functions/notifications';
import { useTableRefresh } from '../../../hooks/TableRefresh';
import { Thumbnail } from '../../items/Thumbnail';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';

export function RelatedPartTable({ partId }: { partId: number }): ReactNode {
  const { refreshId, refreshTable } = useTableRefresh();

  // Construct table columns for this table
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
              <Thumbnail src={part.thumbnail || part.image} />
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
          openDeleteApiForm({
            name: 'delete-related-part',
            url: '/part/related/',
            pk: record.pk,
            title: t`Delete Related Part`,
            successMessage: t`Related part deleted`,
            preFormContent: (
              <Text>{t`Are you sure you want to remove this relationship?`}</Text>
            ),
            onFormSuccess: refreshTable
          });
        }
      }
    ];
  }, []);

  return (
    <InvenTreeTable
      url="/part/related/"
      tableKey="related-part-table"
      refreshId={refreshId}
      params={{
        part: partId
      }}
      rowActions={rowActions}
      columns={tableColumns}
    />
  );
}
