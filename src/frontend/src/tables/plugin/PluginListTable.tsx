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
import { showNotification } from '@mantine/notifications';
import {
  IconCircleCheck,
  IconCircleX,
  IconHelpCircle,
  IconInfoCircle,
  IconPlaylistAdd,
  IconRefresh
} from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { api } from '../../App';
import { ActionButton } from '../../components/buttons/ActionButton';
import { YesNoButton } from '../../components/buttons/YesNoButton';
import { InfoItem } from '../../components/items/InfoItem';
import { DetailDrawer } from '../../components/nav/DetailDrawer';
import { PluginSettingList } from '../../components/settings/SettingList';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
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
import { InvenTreeTable } from '../InvenTreeTable';
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

export function PluginDrawer({ pluginKey }: { pluginKey: Readonly<string> }) {
  const {
    instance: plugin,
    instanceQuery: { isFetching, error }
  } = useInstance<PluginI>({
    endpoint: ApiEndpoints.plugin_list,
    hasPrimaryKey: true,
    pk: pluginKey,
    throwError: true
  });

  if (!pluginKey || isFetching) {
    return <LoadingOverlay visible={true} />;
  }

  if (!plugin || error) {
    return (
      <Text>
        {(error as any)?.response?.status === 404 ? (
          <Trans>Plugin with key {pluginKey} not found</Trans>
        ) : (
          <Trans>An error occurred while fetching plugin details</Trans>
        )}
      </Text>
    );
  }

  return (
    <Stack gap={'xs'}>
      <Card withBorder>
        <Group justify="left">
          <Box></Box>

          <Group gap={'xs'}>
            {plugin && <PluginIcon plugin={plugin} />}
            <Title order={4}>
              {plugin?.meta?.human_name ?? plugin?.name ?? '-'}
            </Title>
          </Group>
        </Group>
      </Card>
      <LoadingOverlay visible={isFetching} overlayProps={{ opacity: 0 }} />

      <Card withBorder>
        <Stack gap="md">
          <Title order={4}>
            <Trans>Plugin information</Trans>
          </Title>
          {plugin.active ? (
            <Stack pos="relative" gap="xs">
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
              <InfoItem
                type="boolean"
                name={t`Active`}
                value={plugin?.active}
              />
            </Stack>
          ) : (
            <Text color="red">{t`Plugin is not active`}</Text>
          )}
        </Stack>
      </Card>

      {plugin.active && (
        <Card withBorder>
          <Stack gap="md">
            <Title order={4}>
              <Trans>Package information</Trans>
            </Title>
            <Stack pos="relative" gap="xs">
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
      )}

      {plugin && plugin?.active && (
        <Card withBorder>
          <Stack gap="md">
            <Title order={4}>
              <Trans>Plugin settings</Trans>
            </Title>
            <PluginSettingList pluginKey={pluginKey} />
          </Stack>
        </Card>
      )}
    </Stack>
  );
}

/**
 * Construct an indicator icon for a single plugin
 */
function PluginIcon({ plugin }: { plugin: PluginI }) {
  if (plugin?.is_installed) {
    if (plugin?.active) {
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

  const [pluginsEnabled, plugins_install_disabled] = useServerApiState(
    (state) => [
      state.server.plugins_enabled,
      state.server.plugins_install_disabled
    ]
  );

  const pluginTableColumns: TableColumn[] = useMemo(
    () => [
      {
        accessor: 'name',
        title: t`Plugin`,
        sortable: true,
        render: function (record: any) {
          if (!record) {
            return;
          }

          return (
            <Group justify="left">
              <PluginIcon plugin={record} />
              <Text>{record.name}</Text>
            </Group>
          );
        }
      },
      {
        accessor: 'active',
        sortable: true,
        title: t`Active`,
        render: (record: any) => <YesNoButton value={record.active} />
      },
      {
        accessor: 'meta.description',
        title: t`Description`,
        sortable: false,

        render: function (record: any) {
          if (record.active) {
            return record?.meta.description;
          } else {
            return (
              <Text
                style={{ fontStyle: 'italic' }}
                size="sm"
              >{t`Description not available`}</Text>
            );
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

  const [selectedPlugin, setSelectedPlugin] = useState<string>('');
  const [activate, setActivate] = useState<boolean>(false);

  const activateModalContent = useMemo(() => {
    return (
      <Stack gap="xs">
        <Alert
          color={activate ? 'green' : 'red'}
          icon={<IconCircleCheck />}
          title={
            activate
              ? t`Confirm plugin activation`
              : t`Confirm plugin deactivation`
          }
        >
          <Text>
            {activate
              ? t`The selected plugin will be activated`
              : t`The selected plugin will be deactivated`}
          </Text>
        </Alert>
      </Stack>
    );
  }, [activate]);

  const activatePluginModal = useEditApiFormModal({
    title: t`Activate Plugin`,
    url: ApiEndpoints.plugin_activate,
    pathParams: { key: selectedPlugin },
    preFormContent: activateModalContent,
    fetchInitialData: false,
    method: 'POST',
    successMessage: activate
      ? `The plugin was activated`
      : `The plugin was deactivated`,
    fields: {
      active: {
        value: activate,
        hidden: true
      }
    },
    table: table
  });

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
              setSelectedPlugin(record.key);
              setActivate(false);
              activatePluginModal.open();
            }
          });
        } else {
          actions.push({
            title: t`Activate`,
            color: 'green',
            icon: <IconCircleCheck />,
            onClick: () => {
              setSelectedPlugin(record.key);
              setActivate(true);
              activatePluginModal.open();
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
            setSelectedPlugin(record.key);
            uninstallPluginModal.open();
          },
          disabled: plugins_install_disabled || false
        });
      }

      // Uninstalled 'package' plugins can be deleted
      if (!record.is_installed) {
        actions.push({
          title: t`Delete`,
          color: 'red',
          icon: <IconCircleX />,
          onClick: () => {
            setSelectedPlugin(record.key);
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
    successMessage: t`Plugin installed successfully`,
    table: table
  });

  const uninstallPluginModal = useEditApiFormModal({
    title: t`Uninstall Plugin`,
    url: ApiEndpoints.plugin_uninstall,
    pathParams: { key: selectedPlugin },
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
        <Stack gap="xs">
          <Text>{t`The selected plugin will be uninstalled.`}</Text>
          <Text>{t`This action cannot be undone.`}</Text>
        </Stack>
      </Alert>
    ),
    successMessage: t`Plugin uninstalled successfully`,
    table: table
  });

  const deletePluginModal = useDeleteApiFormModal({
    url: ApiEndpoints.plugin_list,
    pathParams: { key: selectedPlugin },
    title: t`Delete Plugin`,
    preFormWarning: t`Deleting this plugin configuration will remove all associated settings and data. Are you sure you want to delete this plugin?`,
    table: table
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
          disabled={plugins_install_disabled || false}
        />
      );
    }

    return actions;
  }, [user, pluginsEnabled]);

  return (
    <>
      {activatePluginModal.modal}
      {installPluginModal.modal}
      {uninstallPluginModal.modal}
      {deletePluginModal.modal}
      <DetailDrawer
        title={t`Plugin Detail`}
        size={'50%'}
        renderContent={(pluginKey) => {
          if (!pluginKey) return;
          return <PluginDrawer pluginKey={pluginKey} />;
        }}
      />
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.plugin_list)}
        tableState={table}
        columns={pluginTableColumns}
        props={{
          enableDownload: false,
          rowActions: rowActions,
          onRowClick: (plugin) => navigate(`${plugin.key}/`),
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
