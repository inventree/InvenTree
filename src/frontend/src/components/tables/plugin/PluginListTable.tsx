import { t } from '@lingui/macro';
import { Alert, Group, Stack, Text, Tooltip } from '@mantine/core';
import { modals } from '@mantine/modals';
import { notifications } from '@mantine/notifications';
import {
  IconCircleCheck,
  IconCircleX,
  IconHelpCircle
} from '@tabler/icons-react';
import { useCallback, useMemo } from 'react';

import { api } from '../../../App';
import { ApiPaths } from '../../../enums/ApiEndpoints';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { StylishText } from '../../items/StylishText';
import { TableColumn } from '../Column';
import { InvenTreeTable, InvenTreeTableProps } from '../InvenTreeTable';
import { RowAction } from '../RowActions';

/**
 * Construct an indicator icon for a single plugin
 */
function PluginIcon(plugin: any) {
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
export function PluginListTable({ props }: { props: InvenTreeTableProps }) {
  const table = useTable('plugin');

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
          let url = apiUrl(ApiPaths.plugin_list, plugin_id) + 'activate/';

          const id = 'plugin-activate';

          // Show a progress notification
          notifications.show({
            id: id,
            message: active ? t`Activating plugin` : t`Deactivating plugin`,
            loading: true
          });

          api
            .patch(url, { active: active })
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
  function rowActions(record: any): RowAction[] {
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

    return actions;
  }

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.plugin_list)}
      tableState={table}
      columns={pluginTableColumns}
      props={{
        ...props,
        enableDownload: false,
        params: {
          ...props.params
        },
        rowActions: rowActions,
        customFilters: [
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
  );
}
