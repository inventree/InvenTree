import { t } from '@lingui/core/macro';
import { Alert, Group, Stack, Text, Tooltip } from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import {
  IconCircleCheck,
  IconCircleX,
  IconHelpCircle,
  IconInfoCircle,
  IconPlaylistAdd,
  IconRefresh,
  IconTrash
} from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { ActionButton } from '@lib/components/ActionButton';
import type { RowAction } from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import type { TableColumn } from '@lib/types/Tables';
import { DetailDrawer } from '../../components/nav/DetailDrawer';
import PluginDrawer from '../../components/plugins/PluginDrawer';
import type { PluginInterface } from '../../components/plugins/PluginInterface';
import { useApi } from '../../contexts/ApiContext';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useServerApiState } from '../../states/ServerApiState';
import { useUserState } from '../../states/UserState';
import { BooleanColumn, LinkColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

/**
 * Construct an indicator icon for a single plugin
 */
function PluginIcon({ plugin }: Readonly<{ plugin: PluginInterface }>) {
  if (plugin?.is_installed) {
    if (plugin?.active) {
      return (
        <Tooltip label={t`Plugin is active`}>
          <IconCircleCheck color='green' />
        </Tooltip>
      );
    } else {
      return (
        <Tooltip label={t`Plugin is inactive`}>
          <IconCircleX color='red' />
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
  const api = useApi();
  const table = useTable('plugin');
  const navigate = useNavigate();
  const user = useUserState();

  const { server } = useServerApiState();

  const pluginTableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        title: t`Plugin`,
        sortable: true,
        render: (record: any) => {
          if (!record) {
            return;
          }

          return (
            <Group justify='left'>
              <PluginIcon plugin={record} />
              <Text>{record.name}</Text>
            </Group>
          );
        }
      },
      BooleanColumn({
        accessor: 'active',
        sortable: true,
        title: t`Active`
      }),
      BooleanColumn({
        accessor: 'is_builtin',
        sortable: false,
        title: t`Builtin`
      }),
      BooleanColumn({
        accessor: 'is_mandatory',
        sortable: false,
        title: t`Mandatory`
      }),
      {
        accessor: 'meta.description',
        title: t`Description`,
        sortable: false,
        render: (record: any) => {
          if (record.active) {
            return record?.meta.description;
          } else {
            return (
              <Text
                style={{ fontStyle: 'italic' }}
                size='sm'
              >{t`Description not available`}</Text>
            );
          }
        }
      },
      {
        accessor: 'meta.version',
        title: t`Version`,
        sortable: false,
        render: (record: any) => {
          return record?.meta.version;
        }
      },
      {
        accessor: 'meta.author',
        title: 'Author',
        sortable: false
      },
      LinkColumn({
        accessor: 'meta.website',
        title: t`Website`,
        sortable: false,
        switchable: true
      })
    ];
  }, []);

  const [selectedPlugin, setSelectedPlugin] = useState<any>({});
  const [selectedPluginKey, setSelectedPluginKey] = useState<string>('');
  const [activate, setActivate] = useState<boolean>(false);

  const activateModalContent = useMemo(() => {
    return (
      <Stack gap='xs'>
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

  // Determine available actions for a given plugin
  const rowActions = useCallback(
    (record: any): RowAction[] => {
      // Only superuser can perform plugin actions
      if (!user.isSuperuser() || !server.plugins_enabled) {
        return [];
      }

      return [
        {
          hidden: record.is_mandatory != false || record.active != true,
          title: t`Deactivate`,
          color: 'red',
          icon: <IconCircleX />,
          onClick: () => {
            setSelectedPluginKey(record.key);
            setActivate(false);
            activatePluginModal.open();
          }
        },
        {
          hidden:
            record.is_mandatory != false ||
            !record.is_installed ||
            record.active != false,
          title: t`Activate`,
          tooltip: t`Activate selected plugin`,
          color: 'green',
          icon: <IconCircleCheck />,
          onClick: () => {
            setSelectedPluginKey(record.key);
            setActivate(true);
            activatePluginModal.open();
          }
        },
        {
          hidden: !record.active || !record.is_package || !record.package_name,
          title: t`Update`,
          tooltip: t`Update selected plugin`,
          color: 'blue',
          icon: <IconRefresh />,
          onClick: () => {
            setPluginPackage(record.package_name);
            installPluginModal.open();
          }
        },
        {
          // Uninstall an installed plugin
          // Must be inactive, not a builtin, not a sample, and installed as a package
          hidden:
            !user.isSuperuser() ||
            record.active ||
            record.is_builtin ||
            record.is_mandatory ||
            record.is_sample ||
            !record.is_installed ||
            !record.is_package,
          title: t`Uninstall`,
          tooltip: t`Uninstall selected plugin`,
          color: 'red',
          icon: <IconCircleX />,
          onClick: () => {
            setSelectedPluginKey(record.key);
            uninstallPluginModal.open();
          }
        },
        {
          // Delete a plugin configuration
          // Must be inactive, not a builtin, not a sample, and not installed (i.e. no matching plugin)
          hidden:
            record.active ||
            record.is_builtin ||
            record.is_mandatory ||
            record.is_sample ||
            record.is_installed ||
            !user.isSuperuser(),
          title: t`Delete`,
          tooltip: t`Delete selected plugin configuration`,
          color: 'red',
          icon: <IconTrash />,
          onClick: () => {
            setSelectedPluginKey(record.key);
            deletePluginModal.open();
          }
        }
      ];
    },
    [user, server]
  );

  const [pluginPackage, setPluginPackage] = useState<string>('');

  const activatePluginModal = useEditApiFormModal({
    title: t`Activate Plugin`,
    url: ApiEndpoints.plugin_activate,
    pathParams: { key: selectedPluginKey },
    preFormContent: activateModalContent,
    fetchInitialData: false,
    method: 'PATCH',
    successMessage: activate
      ? t`The plugin was activated`
      : t`The plugin was deactivated`,
    fields: {
      active: {
        hidden: true
      }
    },
    initialData: {
      active: activate
    },
    table: table
  });

  const installPluginModal = useCreateApiFormModal({
    title: t`Install Plugin`,
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
    pathParams: { key: selectedPluginKey },
    fetchInitialData: false,
    timeout: 30000,
    fields: {
      delete_config: {}
    },
    preFormContent: (
      <Alert
        color='red'
        icon={<IconInfoCircle />}
        title={t`Confirm plugin uninstall`}
      >
        <Stack gap='xs'>
          <Text>{t`The selected plugin will be uninstalled.`}</Text>
          <Text>{t`This action cannot be undone`}</Text>
        </Stack>
      </Alert>
    ),
    successMessage: t`Plugin uninstalled successfully`,
    table: table
  });

  const deletePluginModal = useDeleteApiFormModal({
    url: ApiEndpoints.plugin_list,
    pk: selectedPluginKey,
    fetchInitialData: false,
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
    if (!user.isSuperuser() || !server.plugins_enabled) {
      return [];
    }

    return [
      <ActionButton
        key='reload'
        color='green'
        icon={<IconRefresh />}
        tooltip={t`Reload Plugins`}
        onClick={reloadPlugins}
      />,
      <ActionButton
        key='install'
        color='green'
        icon={<IconPlaylistAdd />}
        tooltip={t`Install Plugin`}
        onClick={() => {
          setPluginPackage('');
          installPluginModal.open();
        }}
        disabled={server.plugins_install_disabled || false}
      />
    ];
  }, [user, server]);

  return (
    <>
      {installPluginModal.modal}
      {uninstallPluginModal.modal}
      {deletePluginModal.modal}
      {activatePluginModal.modal}
      <DetailDrawer
        title={`${t`Plugin Detail`} - ${selectedPlugin?.name}`}
        size={'65%'}
        renderContent={(pluginKey) => {
          if (!pluginKey) return;
          return (
            <PluginDrawer
              pluginKey={pluginKey}
              pluginInstance={selectedPlugin}
            />
          );
        }}
      />
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.plugin_list)}
        tableState={table}
        columns={pluginTableColumns}
        props={{
          enableDownload: false,
          rowActions: rowActions,
          onRowClick: (plugin) => {
            setSelectedPlugin(plugin);
            navigate(`${plugin.key}/`);
          },
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
              name: 'mandatory',
              label: t`Mandatory`,
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
