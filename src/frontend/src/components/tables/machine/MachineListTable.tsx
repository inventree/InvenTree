import { t } from '@lingui/macro';
import { Button, Container, Group, Text, Tooltip } from '@mantine/core';
import {
  IconCircleCheck,
  IconCircleX,
  IconHelpCircle
} from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';

import { notYetImplemented } from '../../../functions/notifications';
import { useTableRefresh } from '../../../hooks/TableRefresh';
import { ApiPaths, apiUrl } from '../../../states/ApiState';
import { TableStatusRenderer } from '../../renderers/StatusRenderer';
import { MachineSettingList } from '../../settings/SettingList';
import { TableColumn } from '../Column';
import { BooleanColumn, StatusColumn } from '../ColumnRenderers';
import { InvenTreeTable, InvenTreeTableProps } from '../InvenTreeTable';
import { RowAction } from '../RowActions';

interface MachineI {
  pk: string;
  name: string;
  machine_type: string;
  driver: string;
  initialized: boolean;
  active: boolean;
  status: number;
  status_model: string;
  status_text: string;
  machine_errors: string[];
  is_driver_available: boolean;
}

function MachineDetail({
  machine,
  goBack
}: {
  machine: MachineI;
  goBack: () => void;
}) {
  return (
    <Container>
      <Button onClick={goBack}>Back</Button>
      <Text>{machine.name}</Text>

      <MachineSettingList pk={machine.pk} />
    </Container>
  );
}

/**
 * Table displaying list of available plugins
 */
export function MachineListTable({ props }: { props: InvenTreeTableProps }) {
  const { tableKey, refreshTable } = useTableRefresh('machine');

  const machineTableColumns: TableColumn[] = useMemo(
    () => [
      {
        accessor: 'name',
        title: t`Machine`,
        sortable: true,
        render: function (record: any) {
          // TODO: Add link to machine detail page
          // TODO: Add custom icon
          return (
            <Group position="left">
              <Text>{record.name}</Text>
            </Group>
          );
        }
      },
      {
        accessor: 'machine_type',
        title: t`Machine Type`,
        sortable: true,
        filtering: true
      },
      {
        accessor: 'driver',
        title: t`Machine Driver`,
        sortable: true,
        filtering: true
      },
      BooleanColumn({
        accessor: 'initialized',
        title: t`Initialized`
      }),
      BooleanColumn({
        accessor: 'active',
        title: t`Active`
      }),
      {
        accessor: 'status',
        title: t`Status`,
        sortable: false,
        render: (record) => {
          const renderer = TableStatusRenderer(
            `MachineStatus__${record.status_model}` as any
          );
          if (renderer && record.status !== -1) {
            return renderer(record);
          }
        }
      },
      BooleanColumn({
        accessor: 'is_driver_available',
        title: t`Driver available`
      })
    ],
    []
  );

  // Determine available actions for a given plugin
  function rowActions(record: any): RowAction[] {
    let actions: RowAction[] = [];

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

    return actions;
  }

  const [machineDetail, setMachineDetail] = useState<any>(null);
  const goBack = useCallback(() => setMachineDetail(null), []);

  if (machineDetail) {
    return <MachineDetail machine={machineDetail} goBack={goBack} />;
  }

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.machine_list)}
      tableKey={tableKey}
      columns={machineTableColumns}
      props={{
        ...props,
        enableDownload: false,
        onRowClick: (record) => setMachineDetail(record),
        params: {
          ...props.params
        },
        rowActions: rowActions,
        customFilters: [
          {
            name: 'active',
            label: t`Active`,
            type: 'boolean'
          }
          // TODO: add machine_type choices filter
          // TODO: add driver choices filter
        ]
      }}
    />
  );
}
