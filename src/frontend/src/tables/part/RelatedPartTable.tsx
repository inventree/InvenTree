import { t } from '@lingui/macro';
import { ActionIcon, Group, Text, Tooltip } from '@mantine/core';
import { IconLayersLinked } from '@tabler/icons-react';
import { ReactNode, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { Thumbnail } from '../../components/images/Thumbnail';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { UserRoles } from '../../enums/Roles';
import { openCreateApiForm, openDeleteApiForm } from '../../functions/forms';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowDeleteAction } from '../RowActions';

/**
 * Construct a table listing related parts for a given part
 */
export function RelatedPartTable({ partId }: { partId: number }): ReactNode {
  const table = useTable('relatedparts');

  const navigate = useNavigate();

  const user = useUserState();

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
            <Group
              noWrap={true}
              position="left"
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
  }, [partId]);

  const addRelatedPart = useCallback(() => {
    openCreateApiForm({
      title: t`Add Related Part`,
      url: ApiEndpoints.related_part_list,
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
      onFormSuccess: table.refreshTable
    });
  }, [partId]);

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
  const rowActions = useCallback(
    (record: any) => {
      return [
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.part),
          onClick: () => {
            openDeleteApiForm({
              url: ApiEndpoints.related_part_list,
              pk: record.pk,
              title: t`Delete Related Part`,
              successMessage: t`Related part deleted`,
              preFormWarning: t`Are you sure you want to remove this relationship?`,
              onFormSuccess: table.refreshTable
            });
          }
        })
      ];
    },
    [user]
  );

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.related_part_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        params: {
          part: partId,
          category_detail: true
        },
        rowActions: rowActions,
        tableActions: customActions
      }}
    />
  );
}
