import { t } from '@lingui/macro';
import { ActionIcon, Group, Text, Tooltip } from '@mantine/core';
import { IconLayersLinked } from '@tabler/icons-react';
import { ReactNode, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { openCreateApiForm, openDeleteApiForm } from '../../../functions/forms';
import { useTableRefresh } from '../../../hooks/TableRefresh';
import { ApiPaths, apiUrl } from '../../../states/ApiState';
import { Thumbnail } from '../../items/Thumbnail';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';

export function RelatedPartTable({ partId }: { partId: number }): ReactNode {
  const { tableKey, refreshTable } = useTableRefresh('relatedparts');

  const navigate = useNavigate();

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
        noWrap: true,
        render: (record: any) => {
          let part = getPart(record);
          return (
            <Group
              onClick={() => {
                navigate(`/part/${part.pk}/`);
              }}
            >
              <Thumbnail src={part.thumbnail || part.image} />
              <Text>{part.name}</Text>
            </Group>
          );
        }
      },
      {
        accessor: 'description',
        title: t`Description`,
        ellipsis: true,
        render: (record: any) => {
          return getPart(record).description;
        }
      }
    ];
  }, []);

  const addRelatedPart = useCallback(() => {
    openCreateApiForm({
      name: 'add-related-part',
      title: t`Add Related Part`,
      url: ApiPaths.related_part_list,
      fields: {
        part_1: {
          hidden: true,
          value: partId
        },
        part_2: {
          label: t`Related Part`
        }
      },
      successMessage: t`Related part added`,
      onFormSuccess: refreshTable
    });
  }, []);

  const customActions: ReactNode[] = useMemo(() => {
    // TODO: Hide if user does not have permission to edit parts
    let actions = [];

    actions.push(
      <Tooltip label={t`Add related part`}>
        <ActionIcon radius="sm" onClick={addRelatedPart}>
          <IconLayersLinked />
        </ActionIcon>
      </Tooltip>
    );

    return actions;
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
            url: ApiPaths.related_part_list,
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
      url={apiUrl(ApiPaths.related_part_list)}
      tableKey={tableKey}
      columns={tableColumns}
      props={{
        params: {
          part: partId,
          category_detail: true
        },
        rowActions: rowActions,
        customActionGroups: customActions
      }}
    />
  );
}
