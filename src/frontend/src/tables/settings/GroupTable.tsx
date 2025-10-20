import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import { Accordion, LoadingOverlay, Stack, Text } from '@mantine/core';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '@lib/components/AddItemButton';
import {
  type RowAction,
  RowDeleteAction,
  RowEditAction
} from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import { getDetailUrl } from '@lib/index';
import type { TableColumn } from '@lib/types/Tables';
import { IconUsersGroup } from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';
import { EditApiForm } from '../../components/forms/ApiForm';
import { RoleTable, type RuleSet } from '../../components/items/RoleTable';
import { StylishText } from '../../components/items/StylishText';
import { DetailDrawer } from '../../components/nav/DetailDrawer';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import { InvenTreeTable } from '../InvenTreeTable';

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
            <RoleTable roles={groupRoles} editable />
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
