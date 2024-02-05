import { Trans, t } from '@lingui/macro';
import {
  Alert,
  Box,
  Card,
  Group,
  LoadingOverlay,
  Stack,
  Text,
  Title,
  Tooltip
} from '@mantine/core';
import { modals } from '@mantine/modals';
import { notifications, showNotification } from '@mantine/notifications';
import {
  IconCircleCheck,
  IconCircleX,
  IconHelpCircle,
  IconInfoCircle,
  IconPlaylistAdd,
  IconRefresh
} from '@tabler/icons-react';
import { IconDots } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { api } from '../../App';
import { ActionButton } from '../../components/buttons/ActionButton';
import {
  ActionDropdown,
  EditItemAction
} from '../../components/items/ActionDropdown';
import { InfoItem } from '../../components/items/InfoItem';
import { StylishText } from '../../components/items/StylishText';
import { DetailDrawer } from '../../components/nav/DetailDrawer';
import { PluginSettingList } from '../../components/settings/SettingList';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { openEditApiForm } from '../../functions/forms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import { useTable } from '../../hooks/UseTable';
import { apiUrl, useServerApiState } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { InvenTreeTable, InvenTreeTableProps } from '../InvenTreeTable';
import { RowAction } from '../RowActions';

export interface PluginI {
  pk: number;
  key: string;
  name: string;
  active: boolean;
  is_builtin: boolean;
  is_sample: boolean;
  is_installed: boolean;
  is_package: boolean;
  package_name: string | null;
  meta: {
    author: string | null;
    description: string | null;
    human_name: string | null;
    license: string | null;
    package_path: string | null;
    pub_date: string | null;
    settings_url: string | null;
    slug: string | null;
    version: string | null;
    website: string | null;
  };
  mixins: Record<
    string,
    {
      key: string;
      human_name: string;
    }
  >;
}

export function PluginDrawer({
  id,
  refreshTable
}: {
  id: string;
  refreshTable: () => void;
}) {
  const {
    instance: plugin,
    refreshInstance,
    instanceQuery: { isFetching, error }
  } = useInstance<PluginI>({
    endpoint: ApiEndpoints.plugin_list,
    pk: id,
    throwError: true
  });

  const refetch = useCallback(() => {
    refreshTable();
    refreshInstance();
  }, [refreshTable, refreshInstance]);

  if (isFetching) {
    return <LoadingOverlay visible={true} />;
  }

  if (error) {
    return (
      <Text>
        {(error as any)?.response?.status === 404 ? (
          <Trans>Plugin with id {id} not found</Trans>
        ) : (
          <Trans>An error occurred while fetching plugin details</Trans>
        )}
      </Text>
    );
  }

  return (
    <Stack spacing={'xs'}>
      <Group position="apart">
        <Box></Box>

        <Group spacing={'xs'}>
          {plugin && PluginIcon(plugin)}
          <Title order={4}>{plugin?.meta.human_name || plugin?.name}</Title>
        </Group>

        <ActionDropdown
          tooltip={t`Plugin Actions`}
          icon={<IconDots />}
          actions={[
            EditItemAction({
              tooltip: t`Edit plugin`,
              onClick: () => {
                openEditApiForm({
                  title: t`Edit plugin`,
                  url: ApiEndpoints.plugin_list,
                  pk: id,
                  fields: {
                    active: {}
                  },
                  onClose: refetch
                });
              }
            }),
            {
              name: t`Reload`,
              tooltip: t`Reload`,
              icon: <IconRefresh />,
              onClick: refreshInstance
            }
          ]}
        />
      </Group>

      <LoadingOverlay visible={isFetching} overlayOpacity={0} />

      <Card withBorder>
        <Stack spacing="md">
          <Title order={4}>
            <Trans>Plugin information</Trans>
          </Title>
          <Stack pos="relative" spacing="xs">
            <InfoItem type="text" name={t`Name`} value={plugin?.name} />
            <InfoItem
              type="text"
              name={t`Description`}
              value={plugin?.meta.description}
            />
            <InfoItem
              type="text"
              name={t`Author`}
              value={plugin?.meta.author}
            />
            <InfoItem
              type="text"
              name={t`Date`}
              value={plugin?.meta.pub_date}
            />
            <InfoItem
              type="text"
              name={t`Version`}
              value={plugin?.meta.version}
            />
            <InfoItem type="boolean" name={t`Active`} value={plugin?.active} />
          </Stack>
        </Stack>
      </Card>

      <Card withBorder>
        <Stack spacing="md">
          <Title order={4}>
            <Trans>Package information</Trans>
          </Title>
          <Stack pos="relative" spacing="xs">
            {plugin?.is_package && (
              <InfoItem
                type="text"
                name={t`Package Name`}
                value={plugin?.package_name}
              />
            )}
            <InfoItem
              type="text"
              name={t`Installation Path`}
              value={plugin?.meta.package_path}
            />
            <InfoItem
              type="boolean"
              name={t`Builtin`}
              value={plugin?.is_builtin}
            />
            <InfoItem
              type="boolean"
              name={t`Package`}
              value={plugin?.is_package}
            />
          </Stack>
        </Stack>
      </Card>

      {plugin && plugin.active && (
        <Card withBorder>
          <Stack spacing="md">
            <Title order={4}>
              <Trans>Plugin settings</Trans>
            </Title>
            <PluginSettingList pluginPk={id} />
          </Stack>
        </Card>
      )}
    </Stack>
  );
}

/**
 * Construct an indicator icon for a single plugin
 */
function PluginIcon(plugin: PluginI) {
  if (plugin.is_installed) {
    if (plugin.active) {
      return (
        <Tooltip label={t`Plugin is active`}>
          <IconCircleCheck color="green" />
        </Tooltip>
      );
    } else {
      return (
        <Tooltip label={t`Plugin is inactive`}>
          <IconCircleX color="red" />
        </Tooltip>
      );
    }
  } else {
    return (
      <Tooltip label={t`Plugin is not installed`}>
        <IconHelpCircle />
      </Tooltip>
    );
  }
}

/**
 * Table displaying list of available plugins
 */
export default function PluginListTable() {
  const table = useTable('plugin');
  const navigate = useNavigate();
  const user = useUserState();

  const pluginsEnabled = useServerApiState(
    (state) => state.server.plugins_enabled
  );

  const pluginTableColumns: TableColumn[] = useMemo(
    () => [
      {
        accessor: 'name',
        title: t`Plugin`,
        sortable: true,
        render: function (record: any) {
          // TODO: Add link to plugin detail page
          // TODO: Add custom badges
          return (
            <Group position="left">
              <PluginIcon {...record} />
              <Text>{record.name}</Text>
            </Group>
          );
        }
      },
      {
        accessor: 'meta.description',
        title: t`Description`,
        sortable: false,

        render: function (record: any) {
          if (record.active) {
            return record.meta.description;
          } else {
            return <Text italic>{t`Description not available`}</Text>;
          }
        }
      },
      {
        accessor: 'meta.version',
        title: t`Version`,
        sortable: false

        // TODO: Display date information if available
      },
      {
        accessor: 'meta.author',
        title: 'Author',
        sortable: false
      }
    ],
    []
  );

  const activatePlugin = useCallback(
    (plugin_id: number, plugin_name: string, active: boolean) => {
      modals.openConfirmModal({
        title: (
          <StylishText>
            {active ? t`Activate Plugin` : t`Deactivate Plugin`}
          </StylishText>
        ),
        children: (
          <Alert
            color="green"
            icon={<IconCircleCheck />}
            title={
              active
                ? t`Confirm plugin activation`
                : t`Confirm plugin deactivation`
            }
          >
            <Stack spacing="xs">
              <Text>
                {active
                  ? t`The following plugin will be activated`
                  : t`The following plugin will be deactivated`}
                :
              </Text>
              <Text size="lg" italic>
                {plugin_name}
              </Text>
            </Stack>
          </Alert>
        ),
        labels: {
          cancel: t`Cancel`,
          confirm: t`Confirm`
        },
        onConfirm: () => {
          let url = apiUrl(ApiEndpoints.plugin_activate, plugin_id);

          const id = 'plugin-activate';

          // Show a progress notification
          notifications.show({
            id: id,
            message: active ? t`Activating plugin` : t`Deactivating plugin`,
            loading: true
          });

          api
            .patch(
              url,
              { active: active },
              {
                timeout: 30 * 1000
              }
            )
            .then(() => {
              table.refreshTable();
              notifications.hide(id);
              notifications.show({
                title: t`Plugin updated`,
                message: active
                  ? t`The plugin was activated`
                  : t`The plugin was deactivated`,
                color: 'green'
              });
            })
            .catch((_err) => {
              notifications.hide(id);
              notifications.show({
                title: t`Error`,
                message: t`Error updating plugin`,
                color: 'red'
              });
            });
        }
      });
    },
    []
  );

  // Determine available actions for a given plugin
  const rowActions = useCallback(
    (record: any) => {
      // TODO: Plugin actions should be updated based on on the users's permissions

      let actions: RowAction[] = [];

      if (!record.is_builtin && record.is_installed) {
        if (record.active) {
          actions.push({
            title: t`Deactivate`,
            color: 'red',
            icon: <IconCircleX />,
            onClick: () => {
              activatePlugin(record.pk, record.name, false);
            }
          });
        } else {
          actions.push({
            title: t`Activate`,
            color: 'green',
            icon: <IconCircleCheck />,
            onClick: () => {
              activatePlugin(record.pk, record.name, true);
            }
          });
        }
      }

      // Active 'package' plugins can be updated
      if (record.active && record.is_package && record.package_name) {
        actions.push({
          title: t`Update`,
          color: 'blue',
          icon: <IconRefresh />,
          onClick: () => {
            setPluginPackage(record.package_name);
            installPluginModal.open();
          }
        });
      }

      // Inactive 'package' plugins can be uninstalled
      if (
        !record.active &&
        record.is_installed &&
        record.is_package &&
        record.package_name
      ) {
        actions.push({
          title: t`Uninstall`,
          color: 'red',
          icon: <IconCircleX />,
          onClick: () => {
            setSelectedPlugin(record.pk);
            uninstallPluginModal.open();
          }
        });
      }

      // Uninstalled 'package' plugins can be deleted
      if (!record.is_installed) {
        actions.push({
          title: t`Delete`,
          color: 'red',
          icon: <IconCircleX />,
          onClick: () => {
            setSelectedPlugin(record.pk);
            deletePluginModal.open();
          }
        });
      }

      return actions;
    },
    [user, pluginsEnabled]
  );

  const [pluginPackage, setPluginPackage] = useState<string>('');

  const installPluginModal = useCreateApiFormModal({
    title: t`Install plugin`,
    url: ApiEndpoints.plugin_install,
    timeout: 30000,
    fields: {
      packagename: {},
      url: {},
      version: {},
      confirm: {}
    },
    initialData: {
      packagename: pluginPackage
    },
    closeOnClickOutside: false,
    submitText: t`Install`,
    successMessage: undefined,
    onFormSuccess: (data) => {
      notifications.show({
        title: t`Plugin installed successfully`,
        message: data.result,
        autoClose: 30000,
        color: 'green'
      });

      table.refreshTable();
    }
  });

  const [selectedPlugin, setSelectedPlugin] = useState<number>(-1);

  const uninstallPluginModal = useEditApiFormModal({
    title: t`Uninstall Plugin`,
    url: ApiEndpoints.plugin_uninstall,
    pk: selectedPlugin,
    fetchInitialData: false,
    timeout: 30000,
    fields: {
      delete_config: {}
    },
    preFormContent: (
      <Alert
        color="red"
        icon={<IconInfoCircle />}
        title={t`Confirm plugin uninstall`}
      >
        <Stack spacing="xs">
          <Text>{t`The selected plugin will be uninstalled.`}</Text>
          <Text>{t`This action cannot be undone.`}</Text>
        </Stack>
      </Alert>
    ),
    onFormSuccess: (data) => {
      notifications.show({
        title: t`Plugin uninstalled successfully`,
        message: data.result,
        autoClose: 30000,
        color: 'green'
      });

      table.refreshTable();
    }
  });

  const deletePluginModal = useDeleteApiFormModal({
    url: ApiEndpoints.plugin_list,
    pk: selectedPlugin,
    title: t`Delete Plugin`,
    onFormSuccess: table.refreshTable,
    preFormWarning: t`Deleting this plugin configuration will remove all associated settings and data. Are you sure you want to delete this plugin?`
  });

  const reloadPlugins = useCallback(() => {
    api
      .post(apiUrl(ApiEndpoints.plugin_reload), {
        full_reload: true,
        force_reload: true,
        collect_plugins: true
      })
      .then(() => {
        showNotification({
          title: t`Plugins reloaded`,
          message: t`Plugins were reloaded successfully`,
          color: 'green'
        });
        table.refreshTable();
      });
  }, []);

  // Custom table actions
  const tableActions = useMemo(() => {
    let actions = [];

    if (user.user?.is_superuser && pluginsEnabled) {
      actions.push(
        <ActionButton
          color="green"
          icon={<IconRefresh />}
          tooltip={t`Reload Plugins`}
          onClick={reloadPlugins}
        />
      );

      actions.push(
        <ActionButton
          color="green"
          icon={<IconPlaylistAdd />}
          tooltip={t`Install Plugin`}
          onClick={() => {
            setPluginPackage('');
            installPluginModal.open();
          }}
        />
      );
    }

    return actions;
  }, [user, pluginsEnabled]);

  return (
    <>
      {installPluginModal.modal}
      {uninstallPluginModal.modal}
      {deletePluginModal.modal}
      <DetailDrawer
        title={t`Plugin detail`}
        size={'xl'}
        renderContent={(id) => {
          if (!id) return false;
          return <PluginDrawer id={id} refreshTable={table.refreshTable} />;
        }}
      />
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.plugin_list)}
        tableState={table}
        columns={pluginTableColumns}
        props={{
          enableDownload: false,
          rowActions: rowActions,
          onRowClick: (plugin) => navigate(`${plugin.pk}/`),
          tableActions: tableActions,
          tableFilters: [
            {
              name: 'active',
              label: t`Active`,
              type: 'boolean'
            },
            {
              name: 'builtin',
              label: t`Builtin`,
              type: 'boolean'
            },
            {
              name: 'sample',
              label: t`Sample`,
              type: 'boolean'
            },
            {
              name: 'installed',
              label: t`Installed`,
              type: 'boolean'
            }
          ]
        }}
      />
    </>
  );
}
