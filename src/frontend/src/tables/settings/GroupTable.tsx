import { Trans, t } from '@lingui/macro';
import { Group, LoadingOverlay, Stack, Text, Title } from '@mantine/core';
import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { EditApiForm } from '../../components/forms/ApiForm';
import { PlaceholderPill } from '../../components/items/Placeholder';
import { DetailDrawer } from '../../components/nav/DetailDrawer';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowAction, RowDeleteAction, RowEditAction } from '../RowActions';

export interface GroupDetailI {
  pk: number;
  name: string;
}

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
    endpoint: ApiEndpoints.group_list,
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
          url: ApiEndpoints.group_list,
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

  const openDetailDrawer = useCallback(
    (pk: number) => navigate(`group-${pk}/`),
    []
  );

  const columns: TableColumn<GroupDetailI>[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        sortable: true,
        title: t`Name`
      }
    ];
  }, []);

  const rowActions = useCallback((record: GroupDetailI): RowAction[] => {
    return [
      RowEditAction({
        onClick: () => openDetailDrawer(record.pk)
      }),
      RowDeleteAction({
        onClick: () => {
          setSelectedGroup(record.pk), deleteGroup.open();
        }
      })
    ];
  }, []);

  const [selectedGroup, setSelectedGroup] = useState<number | undefined>(
    undefined
  );

  const deleteGroup = useDeleteApiFormModal({
    url: ApiEndpoints.group_list,
    pk: selectedGroup,
    title: t`Delete group`,
    successMessage: t`Group deleted`,
    onFormSuccess: table.refreshTable,
    preFormWarning: t`Are you sure you want to delete this group?`
  });

  const newGroup = useCreateApiFormModal({
    url: ApiEndpoints.group_list,
    title: t`Add group`,
    fields: { name: {} },
    onFormSuccess: table.refreshTable
  });

  const tableActions = useMemo(() => {
    let actions = [];

    actions.push(
      <AddItemButton
        key={'add-group'}
        onClick={() => newGroup.open()}
        tooltip={t`Add group`}
      />
    );

    return actions;
  }, []);

  return (
    <>
      {newGroup.modal}
      {deleteGroup.modal}
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
        url={apiUrl(ApiEndpoints.group_list)}
        tableState={table}
        columns={columns}
        props={{
          rowActions: rowActions,
          tableActions: tableActions,
          onRowClick: (record) => openDetailDrawer(record.pk)
        }}
      />
    </>
  );
}
