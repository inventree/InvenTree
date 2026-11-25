import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import {
  Accordion,
  Group,
  LoadingOverlay,
  Stack,
  Table,
  Text
} from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import { useCallback, useMemo, useState } from 'react';

import { ActionButton } from '@lib/components/ActionButton';
import { AddItemButton } from '@lib/components/AddItemButton';
import {
  type RowAction,
  RowDeleteAction,
  RowEditAction
} from '@lib/components/RowActions';
import { StylishText } from '@lib/components/StylishText';
import { DetailDrawer } from '@lib/components/nav/DetailDrawer';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import { getDetailUrl } from '@lib/functions/Navigation';
import useTable from '@lib/hooks/UseTable';
import type { ApiFormModalProps } from '@lib/index';
import type { TableColumn, TableState } from '@lib/types/Tables';
import { IconUserMinus, IconUsersGroup } from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../App';
import { EditApiForm } from '../../components/forms/ApiForm';
import { StandaloneField } from '../../components/forms/StandaloneField';
import { RoleTable, type RuleSet } from '../../components/items/RoleTable';
import { InvenTreeTable } from '../../components/tables/InvenTreeTable';
import { showApiErrorMessage } from '../../functions/notifications';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import { useUserState } from '../../states/UserState';

export interface GroupDetailI {
  pk: number;
  name: string;
}

interface GroupMemberI {
  pk: number;
  username: string;
  first_name?: string;
  last_name?: string;
  email?: string;
}

/**
 * Display (and optionally edit) the users which belong to a group.
 *
 * Membership changes are made via the existing user detail endpoint
 * (PATCH /api/user/<pk>/ with 'group_ids'), so the same permission checks
 * apply as when editing a user's groups from the "Edit User" drawer.
 */
function GroupUsers({
  groupId,
  users,
  onChange
}: Readonly<{
  groupId: number;
  users: GroupMemberI[];
  onChange: () => void;
}>) {
  const user = useUserState();

  // Membership is edited via the user endpoint, which requires staff + user change permission
  const canEdit: boolean = useMemo(
    () => user.isStaff() && user.hasChangePermission(ModelType.user),
    [user]
  );

  const [busy, setBusy] = useState<boolean>(false);

  // Used to reset the "add user" field after a selection is made
  const [fieldKey, setFieldKey] = useState<number>(0);

  const sortedUsers = useMemo(
    () =>
      [...(users ?? [])].sort((a, b) => a.username.localeCompare(b.username)),
    [users]
  );

  // Fetch the user's current groups, apply the modification, and save
  const updateMembership = useCallback(
    async (userId: number, add: boolean) => {
      if (!canEdit || busy) return;

      setBusy(true);

      try {
        const response = await api.get(apiUrl(ApiEndpoints.user_list, userId));
        const current: number[] = (response.data?.groups ?? []).map(
          (g: any) => g.pk
        );

        if (add === current.includes(groupId)) {
          // Nothing to do (already a member / already removed)
          return;
        }

        const group_ids = add
          ? [...current, groupId]
          : current.filter((pk) => pk !== groupId);

        await api.patch(apiUrl(ApiEndpoints.user_list, userId), {
          group_ids
        });

        showNotification({
          title: add ? t`User added` : t`User removed`,
          message: add ? t`User added to group` : t`User removed from group`,
          color: 'green'
        });
      } catch (error) {
        showApiErrorMessage({
          error: error,
          title: t`Error updating group membership`
        });
      } finally {
        setBusy(false);
        onChange();
      }
    },
    [canEdit, busy, groupId, onChange]
  );

  const memberIds: number[] = useMemo(
    () => sortedUsers.map((u) => u.pk),
    [sortedUsers]
  );

  return (
    <Stack gap='xs'>
      <LoadingOverlay visible={busy} />
      {canEdit && (
        <StandaloneField
          key={`group-add-user-${fieldKey}`}
          fieldName='user'
          fieldDefinition={{
            field_type: 'related field',
            label: t`Add User`,
            description: t`Select a user to add to this group`,
            api_url: apiUrl(ApiEndpoints.user_list),
            model: ModelType.user,
            required: false,
            adjustFilters: (value) => ({ ...value.filters, is_active: true }),
            onValueChange: (value: any) => {
              if (!value) return;
              const pk = Number(value);
              setFieldKey((k) => k + 1);
              if (!memberIds.includes(pk)) {
                updateMembership(pk, true);
              }
            }
          }}
        />
      )}
      {sortedUsers.length === 0 ? (
        <Text c='dimmed' fs='italic'>
          <Trans>No users in this group</Trans>
        </Text>
      ) : (
        <Table striped>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>
                <Trans>Username</Trans>
              </Table.Th>
              <Table.Th>
                <Trans>Name</Trans>
              </Table.Th>
              <Table.Th>
                <Trans>Email</Trans>
              </Table.Th>
              {canEdit && <Table.Th />}
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {sortedUsers.map((member) => (
              <Table.Tr key={`group-user-${member.pk}`}>
                <Table.Td>{member.username}</Table.Td>
                <Table.Td>
                  {[member.first_name, member.last_name]
                    .filter(Boolean)
                    .join(' ')}
                </Table.Td>
                <Table.Td>{member.email}</Table.Td>
                {canEdit && (
                  <Table.Td>
                    <Group justify='right'>
                      <ActionButton
                        icon={<IconUserMinus />}
                        color='red'
                        tooltip={t`Remove user from group`}
                        disabled={busy}
                        onClick={() => updateMembership(member.pk, false)}
                      />
                    </Group>
                  </Table.Td>
                )}
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      )}
    </Stack>
  );
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
    params: {
      permission_detail: true,
      role_detail: true,
      user_detail: true
    }
  });

  const groupRoles: RuleSet[] = useMemo(() => {
    return instance?.roles ?? [];
  }, [instance]);

  // Only block the drawer on the initial load, so that refreshing the group
  // (e.g. after a membership change) does not collapse the open panel
  if (isFetching && !instance?.pk) {
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
      <Accordion defaultValue={'details'}>
        <Accordion.Item key='details' value='details'>
          <Accordion.Control>
            <StylishText size='lg'>
              <Trans>Group Details</Trans>
            </StylishText>
          </Accordion.Control>
          <Accordion.Panel>
            <EditApiForm
              props={{
                url: ApiEndpoints.group_list,
                pk: id,
                fields: {
                  name: {
                    label: t`Name`,
                    description: t`Name of the user group`
                  }
                },
                onFormSuccess: () => {
                  refreshTable();
                  refreshInstance();
                }
              }}
              id={`group-detail-drawer-${id}`}
            />
          </Accordion.Panel>
        </Accordion.Item>

        <Accordion.Item key='roles' value='roles'>
          <Accordion.Control>
            <StylishText size='lg'>
              <Trans>Group Roles</Trans>
            </StylishText>
          </Accordion.Control>
          <Accordion.Panel>
            <RoleTable roles={groupRoles} editable />
          </Accordion.Panel>
        </Accordion.Item>

        <Accordion.Item key='users' value='users'>
          <Accordion.Control>
            <StylishText size='lg'>
              <Trans>Group Users</Trans>
            </StylishText>
          </Accordion.Control>
          <Accordion.Panel>
            <GroupUsers
              groupId={Number(id)}
              users={instance?.users ?? []}
              onChange={() => {
                refreshInstance();
                refreshTable();
              }}
            />
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>
    </Stack>
  );
}

/**
 * Table for displaying list of groups
 */
export function GroupTable({
  directLink = false
}: Readonly<{ directLink?: boolean }>) {
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
        }),
        {
          icon: <IconUsersGroup />,
          title: t`Open Profile`,
          onClick: () => {
            navigate(getDetailUrl(ModelType.group, record.pk));
          }
        }
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

  const newGroup = useCreateApiFormModal(groupFields(table));

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

  // Determine whether the GroupTable is editable
  const editable: boolean = useMemo(
    () => !directLink && user.isStaff() && user.hasChangeRole(UserRoles.admin),
    [user, directLink]
  );

  return (
    <>
      {editable && newGroup.modal}
      {editable && deleteGroup.modal}
      {editable && (
        <DetailDrawer
          size='xl'
          title={t`Edit Group`}
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
      )}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.group_list)}
        tableState={table}
        columns={columns}
        props={{
          rowActions: editable ? rowActions : undefined,
          tableActions: editable ? tableActions : undefined,
          modelType: directLink ? ModelType.group : undefined,
          onRowClick: editable
            ? (record) => openDetailDrawer(record.pk)
            : undefined
        }}
      />
    </>
  );
}

export function groupFields(table?: TableState): ApiFormModalProps {
  return {
    url: ApiEndpoints.group_list,
    title: t`Add Group`,
    fields: {
      name: {
        label: t`Name`,
        description: t`Name of the user group`
      }
    },
    table: table ?? undefined
  };
}
