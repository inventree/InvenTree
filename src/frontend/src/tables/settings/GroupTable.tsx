import { Trans, t } from '@lingui/macro';
import {
  Accordion,
  Group,
  LoadingOverlay,
  Pill,
  PillGroup,
  Stack,
  Text,
  Title
} from '@mantine/core';
import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import AdminButton from '../../components/buttons/AdminButton';
import { EditApiForm } from '../../components/forms/ApiForm';
import { DetailDrawer } from '../../components/nav/DetailDrawer';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import type { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';
import { type RowAction, RowDeleteAction, RowEditAction } from '../RowActions';

export interface GroupDetailI {
  pk: number;
  name: string;
}

export function GroupDrawer({
  id,
  refreshTable
}: Readonly<{
  id: string;
  refreshTable: () => void;
}>) {
  const {
    instance,
    refreshInstance,
    instanceQuery: { isFetching, error }
  } = useInstance({
    endpoint: ApiEndpoints.group_list,
    pk: id,
    throwError: true,
    params: {
      permission_detail: true
    }
  });

  const permissionsAccordion = useMemo(() => {
    if (!instance?.permissions) return null;

    const data = instance.permissions;
    return (
      <Accordion w={'100%'}>
        {Object.keys(data).map((key) => (
          <Accordion.Item key={key} value={key}>
            <Accordion.Control>
              <Pill>{instance.permissions[key].length}</Pill> {key}
            </Accordion.Control>
            <Accordion.Panel>
              <PillGroup>
                {data[key].map((perm: string) => (
                  <Pill key={perm}>{perm}</Pill>
                ))}
              </PillGroup>
            </Accordion.Panel>
          </Accordion.Item>
        ))}
      </Accordion>
    );
  }, [instance]);

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
      <Group justify='space-between'>
        <Title order={5}>
          <Trans>Permission set</Trans>
        </Title>
        <AdminButton model={ModelType.group} id={instance.pk} />
      </Group>
      <Group>{permissionsAccordion}</Group>
    </Stack>
  );
}

/**
 * Table for displaying list of groups
 */
export function GroupTable() {
  const table = useTable('groups');
  const navigate = useNavigate();
  const user = useUserState();

  const openDetailDrawer = useCallback(
    (pk: number) => {
      if (user.hasChangePermission(ModelType.group)) {
        navigate(`group-${pk}/`);
      }
    },
    [user]
  );

  const columns: TableColumn<GroupDetailI>[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        sortable: true,
        title: t`Name`,
        switchable: false
      }
    ];
  }, []);

  const rowActions = useCallback(
    (record: GroupDetailI): RowAction[] => {
      return [
        RowEditAction({
          onClick: () => openDetailDrawer(record.pk),
          hidden: !user.hasChangePermission(ModelType.group)
        }),
        RowDeleteAction({
          hidden: !user.hasDeletePermission(ModelType.group),
          onClick: () => {
            setSelectedGroup(record.pk);
            deleteGroup.open();
          }
        })
      ];
    },
    [user]
  );

  const [selectedGroup, setSelectedGroup] = useState<number>(-1);

  const deleteGroup = useDeleteApiFormModal({
    url: ApiEndpoints.group_list,
    pk: selectedGroup,
    title: t`Delete group`,
    successMessage: t`Group deleted`,
    table: table,
    preFormWarning: t`Are you sure you want to delete this group?`
  });

  const newGroup = useCreateApiFormModal({
    url: ApiEndpoints.group_list,
    title: t`Add group`,
    fields: { name: {} },
    table: table
  });

  const tableActions = useMemo(() => {
    const actions = [];

    actions.push(
      <AddItemButton
        key={'add-group'}
        onClick={() => newGroup.open()}
        tooltip={t`Add group`}
        hidden={!user.hasAddPermission(ModelType.group)}
      />
    );

    return actions;
  }, [user]);

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
