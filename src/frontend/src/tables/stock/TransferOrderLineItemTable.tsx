import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import type { TableColumn } from '@lib/types/Tables';
import { t } from '@lingui/core/macro';
import { Group } from '@mantine/core';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import { RenderPartColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import RowExpansionIcon from '../RowExpansionIcon';

export default function SalesOrderLineItemTable({
  orderId,
  orderDetailRefresh,
  editable
}: Readonly<{
  orderId: number;
  orderDetailRefresh: () => void;
  editable: boolean;
}>) {
  const navigate = useNavigate();
  const user = useUserState();
  const table = useTable('transfer-order-line-item');

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'part',
        sortable: true,
        switchable: false,
        minWidth: 175,
        render: (record: any) => {
          return (
            <Group wrap='nowrap'>
              {record.part_detail?.virtual || (
                <RowExpansionIcon
                  enabled={record.allocated}
                  expanded={table.isRowExpanded(record.pk)}
                />
              )}
              <RenderPartColumn part={record.part_detail} />
            </Group>
          );
        }
      },
      {
        accessor: 'part_detail.IPN',
        title: t`IPN`,
        switchable: true
      }
    ];
  }, [table.isRowExpanded]);

  return (
    <>
      {/* {editLine.modal} */}
      {/* {deleteLine.modal} */}
      {/* {newLine.modal} */}
      {/* {newBuildOrder.modal} */}
      {/* {allocateBySerials.modal} */}
      {/* {allocateStock.modal} */}
      {/* {orderPartsWizard.wizard} */}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.transfser_order_line_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          enableSelection: true,
          enableDownload: true,
          params: {
            order: orderId,
            part_detail: true
          }
          //   rowActions: rowActions,
          //   tableActions: tableActions,
          //   tableFilters: tableFilters,
          //   rowExpansion: rowExpansion
        }}
      />
    </>
  );
}
