import { Trans, t } from '@lingui/macro';
import { Group, LoadingOverlay, Stack, Text, Title } from '@mantine/core';
import { useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { ApiPaths } from '../../../enums/ApiEndpoints';
import {
  openCreateApiForm,
  openDeleteApiForm,
  openEditApiForm
} from '../../../functions/forms';
import { useInstance } from '../../../hooks/UseInstance';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { AddItemButton } from '../../buttons/AddItemButton';
import { EditApiForm } from '../../forms/ApiForm';
import { PlaceholderPill } from '../../items/Placeholder';
import { DetailDrawer } from '../../nav/DetailDrawer';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowAction, RowDeleteAction, RowEditAction } from '../RowActions';

export function GroupDrawer({
  id,
  refreshTable
}: {
  id: string;
  refreshTable: () => void;
}) {
  const {
    refreshInstance,
    instanceQuery: { isFetching, error }
  } = useInstance({
    endpoint: ApiPaths.group_list,
    pk: id,
    throwError: true
  });

  if (isFetching) {
    return <LoadingOverlay visible={true} />;
  }

  if (error) {
    return (
      <Text>
        {(error as any)?.response?.status === 404 ? (
          <Trans>Group with id {id} not found</Trans>
        ) : (
          <Trans>An error occurred while fetching group details</Trans>
        )}
      </Text>
    );
  }

  return (
    <Stack>
      <EditApiForm
        props={{
          url: ApiPaths.group_list,
          pk: id,
          fields: {
            name: {}
          },
          onFormSuccess: () => {
            refreshTable();
            refreshInstance();
          }
        }}
        id={`group-detail-drawer-${id}`}
      />

      <Title order={5}>
        <Trans>Permission set</Trans>
      </Title>
      <Group>
        <PlaceholderPill />
      </Group>
    </Stack>
  );
}

/**
 * Table for displaying list of groups
 */
export function GroupTable() {
  const table = useTable('groups');
  const navigate = useNavigate();

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        sortable: true,
        title: t`Name`
      }
    ];
  }, []);

  const rowActions = useCallback((record: any): RowAction[] => {
    return [
      RowEditAction({
        onClick: () => {
          openEditApiForm({
            url: ApiPaths.group_list,
            pk: record.pk,
            title: t`Edit group`,
            fields: {
              name: {}
            },
            onFormSuccess: table.refreshTable,
            successMessage: t`Group updated`
          });
        }
      }),
      RowDeleteAction({
        onClick: () => {
          openDeleteApiForm({
            url: ApiPaths.group_list,
            pk: record.pk,
            title: t`Delete group`,
            successMessage: t`Group deleted`,
            onFormSuccess: table.refreshTable,
            preFormWarning: t`Are you sure you want to delete this group?`
          });
        }
      })
    ];
  }, []);

  const addGroup = useCallback(() => {
    openCreateApiForm({
      url: ApiPaths.group_list,
      title: t`Add group`,
      fields: { name: {} },
      onFormSuccess: table.refreshTable,
      successMessage: t`Added group`
    });
  }, []);

  const tableActions = useMemo(() => {
    let actions = [];

    actions.push(
      <AddItemButton
        key={'add-group'}
        onClick={addGroup}
        tooltip={t`Add group`}
      />
    );

    return actions;
  }, []);

  return (
    <>
      <DetailDrawer
        title={t`Edit group`}
        renderContent={(id) => {
          if (!id || !id.startsWith('group-')) return false;
          return (
            <GroupDrawer
              id={id.replace('group-', '')}
              refreshTable={table.refreshTable}
            />
          );
        }}
      />
      <InvenTreeTable
        url={apiUrl(ApiPaths.group_list)}
        tableState={table}
        columns={columns}
        props={{
          rowActions: rowActions,
          customActionGroups: tableActions,
          onRowClick: (record) => navigate(`group-${record.pk}/`)
        }}
      />
    </>
  );
}
