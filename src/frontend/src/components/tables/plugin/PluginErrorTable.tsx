import { Trans, t } from '@lingui/macro';
import {
  Alert,
  Box,
  Card,
  Code,
  Flex,
  Group,
  LoadingOverlay,
  Stack,
  Text,
  Title,
  Tooltip
} from '@mantine/core';
import { modals } from '@mantine/modals';
import { notifications } from '@mantine/notifications';
import {
  IconCircleCheck,
  IconCircleX,
  IconHelpCircle,
  IconRefresh
} from '@tabler/icons-react';
import { IconDots } from '@tabler/icons-react';
import { useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { api } from '../../../App';
import { ApiPaths } from '../../../enums/ApiEndpoints';
import { openEditApiForm } from '../../../functions/forms';
import { useTableRefresh } from '../../../hooks/TableRefresh';
import { useInstance } from '../../../hooks/UseInstance';
import { apiUrl } from '../../../states/ApiState';
import { ActionDropdown, EditItemAction } from '../../items/ActionDropdown';
import { StylishText } from '../../items/StylishText';
import { YesNoButton } from '../../items/YesNoButton';
import { DetailDrawer } from '../../nav/DetailDrawer';
import { PluginSettingList } from '../../settings/SettingList';
import { TableColumn } from '../Column';
import { InvenTreeTable, InvenTreeTableProps } from '../InvenTreeTable';
import { RowAction } from '../RowActions';

export interface PluginRegistryErrorI {
  stage: string;
  name: string;
  message: string;
}

/**
 * Table displaying list of plugin registry errors
 */
export function PluginErrorTable({ props }: { props: InvenTreeTableProps }) {
  const { tableKey, refreshTable } = useTableRefresh('registryErrors');

  const registryErrorTableColumns: TableColumn<PluginRegistryErrorI>[] =
    useMemo(
      () => [
        {
          accessor: 'stage',
          title: t`Stage`
        },
        {
          accessor: 'name',
          title: t`Name`
        },
        {
          accessor: 'message',
          title: t`Message`,
          render: (row) => <Code>{row.message}</Code>
        }
      ],
      []
    );

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.plugin_registry_status)}
      tableKey={tableKey}
      columns={registryErrorTableColumns}
      props={{
        ...props,
        dataFormatter: (data: any) => data.registry_errors,
        enableDownload: false,
        enableFilters: false,
        enableSearch: false,
        params: {
          ...props.params
        }
      }}
    />
  );
}
