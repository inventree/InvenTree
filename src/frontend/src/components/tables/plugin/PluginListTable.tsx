import { t } from '@lingui/macro';
import { Group, Text, Tooltip } from '@mantine/core';
import {
  IconCircleCheck,
  IconCircleX,
  IconHelpCircle
} from '@tabler/icons-react';
import { useMemo } from 'react';

import { notYetImplemented } from '../../../functions/notifications';
import { useTableRefresh } from '../../../hooks/TableRefresh';
import { ApiPaths, apiUrl } from '../../../states/ApiState';
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
  const { tableKey, refreshTable } = useTableRefresh('plugin');

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
        switchable: true,
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
        sortable: false,
        switchable: true
        // TODO: Display date information if available
      },
      {
        accessor: 'meta.author',
        title: 'Author',
        sortable: false,
        switchable: true
      }
    ],
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
          onClick: () => {
            notYetImplemented();
          }
        });
      } else {
        actions.push({
          title: t`Activate`,
          onClick: () => {
            notYetImplemented();
          }
        });
      }
    }

    return actions;
  }

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.plugin_list)}
      tableKey={tableKey}
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
