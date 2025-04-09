import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import {
  Accordion,
  Button,
  Checkbox,
  Group,
  LoadingOverlay,
  Stack,
  Table,
  Text,
  Tooltip
} from '@mantine/core';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { notifications } from '@mantine/notifications';
import { IconCircleCheck, IconReload } from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../App';
import { AddItemButton } from '../../components/buttons/AddItemButton';
import { EditApiForm } from '../../components/forms/ApiForm';
import { StylishText } from '../../components/items/StylishText';
import { DetailDrawer } from '../../components/nav/DetailDrawer';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
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

interface RuleSet {
  pk: number;
  name: string;
  label: string;
  group: number;
  can_view: boolean;
  can_add: boolean;
  can_change: boolean;
  can_delete: boolean;
  edited?: boolean;
}

function RoleTable({
  roles
}: {
  roles: RuleSet[];
}) {
  const [rulesets, setRulesets] = useState<RuleSet[]>(roles);

  useEffect(() => {
    setRulesets(roles);
  }, [roles]);

  const edited = useMemo(() => rulesets.some((r) => r.edited), [rulesets]);

  // Ensure the rulesets are always displayed in the same order
  const sortedRulesets = useMemo(() => {
    return rulesets.sort((a, b) => (a.label > b.label ? 1 : -1));
  }, [rulesets]);

  // Change the edited state of the ruleset
  const onToggle = useCallback((rule: RuleSet, field: string) => {
    setRulesets((prev) => {
      const updated = prev.map((r) => {
        if (r.pk === rule.pk) {
          return {
            ...r,
            [field]: !(r as any)[field],
            edited: true
          };
        }
        return r;
      });
      return updated;
    });
  }, []);

  const onSave = async (rulesets: RuleSet[]) => {
    notifications.show({
      id: 'group-roles-update',
      title: t`Updating`,
      message: t`Updating group roles`,
      loading: true,
      color: 'blue',
      autoClose: false
    });

    for (const ruleset of rulesets.filter((r) => r.edited)) {
      await api
        .patch(apiUrl(ApiEndpoints.ruleset_list, ruleset.pk), {
          can_view: ruleset.can_view,
          can_add: ruleset.can_add,
          can_change: ruleset.can_change,
          can_delete: ruleset.can_delete
        })
        .then(() => {
          // Mark this ruleset as "not edited"
          setRulesets((prev) => {
            const updated = prev.map((r) => {
              if (r.pk === ruleset.pk) {
                return {
                  ...r,
                  edited: false
                };
              }
              return r;
            });
            return updated;
          });
        })
        .catch((error) => {
          console.error(error);
        });
    }

    notifications.update({
      id: 'group-roles-update',
      title: t`Updated`,
      message: t`Group roles updated`,
      autoClose: 2000,
      color: 'green',
      icon: <IconCircleCheck />,
      loading: false
    });
  };

  return (
    <>
      <Stack gap='xs'>
        <Table striped withColumnBorders withRowBorders withTableBorder>
          <Table.Thead>
            <Table.Th>
              <Text fw={700}>
                <Trans>Role</Trans>
              </Text>
            </Table.Th>
            <Table.Th>
              <Text fw={700}>
                <Trans>View</Trans>
              </Text>
            </Table.Th>
            <Table.Th>
              <Text fw={700}>
                <Trans>Change</Trans>
              </Text>
            </Table.Th>
            <Table.Th>
              <Text fw={700}>
                <Trans>Add</Trans>
              </Text>
            </Table.Th>
            <Table.Th>
              <Text fw={700}>
                <Trans>Delete</Trans>
              </Text>
            </Table.Th>
          </Table.Thead>
          <Table.Tbody>
            {sortedRulesets.map((rule) => (
              <Table.Tr key={rule.pk}>
                <Table.Td>
                  <Group gap='xs'>
                    <Text>{rule.label}</Text>
                    {rule.edited && <Text>*</Text>}
                  </Group>
                </Table.Td>
                <Table.Td>
                  <Checkbox
                    checked={rule.can_view}
                    onChange={() => onToggle(rule, 'can_view')}
                  />
                </Table.Td>
                <Table.Td>
                  <Checkbox
                    checked={rule.can_change}
                    onChange={() => onToggle(rule, 'can_change')}
                  />
                </Table.Td>
                <Table.Td>
                  <Checkbox
                    checked={rule.can_add}
                    onChange={() => onToggle(rule, 'can_add')}
                  />
                </Table.Td>
                <Table.Td>
                  <Checkbox
                    checked={rule.can_delete}
                    onChange={() => onToggle(rule, 'can_delete')}
                  />
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
        <Group justify='right'>
          <Tooltip label={t`Reset group roles`} disabled={!edited}>
            <Button
              color='red'
              onClick={() => {
                setRulesets(roles);
              }}
              disabled={!edited}
              leftSection={<IconReload />}
            >
              {t`Reset`}
            </Button>
          </Tooltip>
          <Tooltip label={t`Save group roles`} disabled={!edited}>
            <Button
              color='green'
              onClick={() => {
                onSave(rulesets);
              }}
              disabled={!edited}
              leftSection={<IconCircleCheck />}
            >
              {t`Save`}
            </Button>
          </Tooltip>
        </Group>
      </Stack>
    </>
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
    throwError: true,
    params: {
      permission_detail: true,
      role_detail: true,
      user_detail: true
    }
  });

  const groupRoles: RuleSet[] = useMemo(() => {
    return instance?.roles ?? [];
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
            <RoleTable roles={groupRoles} />
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
    title: t`Add Group`,
    fields: {
      name: {
        label: t`Name`,
        description: t`Name of the user group`
      }
    },
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
      {user.hasViewRole(UserRoles.admin) && (
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
          rowActions:
            user.hasChangeRole(UserRoles.admin) && !directLink
              ? rowActions
              : undefined,
          tableActions: tableActions,
          modelType: directLink ? ModelType.group : undefined,
          onRowClick:
            user.hasChangeRole(UserRoles.admin) && !directLink
              ? (record) => openDetailDrawer(record.pk)
              : undefined
        }}
      />
    </>
  );
}
