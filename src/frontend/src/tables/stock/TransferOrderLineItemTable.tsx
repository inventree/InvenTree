import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { AddItemButton, ProgressBar, UserRoles } from '@lib/index';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { t } from '@lingui/core/macro';
import { Group, Text } from '@mantine/core';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTransferOrderLineItemFields } from '../../forms/TransferOrderForms';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import {
  DateColumn,
  DecimalColumn,
  DescriptionColumn,
  LinkColumn,
  ProjectCodeColumn,
  RenderPartColumn
} from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import RowExpansionIcon from '../RowExpansionIcon';

export default function TransferOrderLineItemTable({
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
      },
      DescriptionColumn({
        accessor: 'part_detail.description'
      }),
      {
        accessor: 'reference',
        sortable: false,
        switchable: true
      },
      ProjectCodeColumn({}),
      DecimalColumn({
        accessor: 'quantity',
        sortable: true
      }),
      DateColumn({
        accessor: 'target_date',
        sortable: true,
        title: t`Target Date`
      }),
      {
        accessor: 'stock',
        title: t`Available Stock`,
        render: (record: any) => {
          return <>TODO</>;
        }
      },
      {
        accessor: 'allocated',
        sortable: true,
        render: (record: any) => {
          if (record.part_detail?.virtual) {
            return <Text size='sm' fs='italic'>{t`Virtual part`}</Text>;
          }

          return (
            <ProgressBar
              progressLabel={true}
              value={record.allocated}
              maximum={record.quantity}
            />
          );
        }
      },
      {
        accessor: 'transferred',
        title: t`Transferred`,
        sortable: true,
        render: (record: any) => {
          return <>TODO</>;
        }
      },
      {
        accessor: 'notes'
      },
      LinkColumn({
        accessor: 'link'
      })
    ];
  }, [table.isRowExpanded]);

  const [initialData, setInitialData] = useState({});

  const createLineFields = useTransferOrderLineItemFields({
    orderId: orderId,
    create: true
  });

  const newLine = useCreateApiFormModal({
    url: ApiEndpoints.transfer_order_line_list,
    title: t`Add Line Item`,
    fields: createLineFields,
    initialData: {
      ...initialData
    },
    onFormSuccess: orderDetailRefresh,
    table: table
  });

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add-to-line-item'
        tooltip={t`Add Line Item`}
        onClick={() => {
          setInitialData({
            order: orderId
          });
          newLine.open();
        }}
        hidden={!editable || !user.hasAddRole(UserRoles.transfer_order)}
      />
      //   <ActionButton
      //     key='order-parts'
      //     hidden={!user.hasAddRole(UserRoles.purchase_order)}
      //     disabled={!table.hasSelectedRecords}
      //     tooltip={t`Order Parts`}
      //     icon={<IconShoppingCart />}
      //     color='blue'
      //     onClick={() => {
      //       setPartsToOrder(table.selectedRecords.map((r) => r.part_detail));
      //       orderPartsWizard.openWizard();
      //     }}
      //   />,
      //   <ActionButton
      //     key='allocate-stock'
      //     tooltip={t`Allocate Stock`}
      //     icon={<IconArrowRight />}
      //     disabled={!table.hasSelectedRecords}
      //     color='green'
      //     onClick={() => {
      //       setSelectedItems(
      //         table.selectedRecords.filter((r) => r.allocated < r.quantity)
      //       );
      //       allocateStock.open();
      //     }}
      //   />
    ];
  }, [user, orderId, table.hasSelectedRecords, table.selectedRecords]);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'allocated',
        label: t`Allocated`,
        description: t`Show lines which are fully allocated`
      },
      {
        name: 'completed',
        label: t`Completed`,
        description: t`Show lines which are completed`
      }
    ];
  }, []);

  return (
    <>
      {/* {editLine.modal} */}
      {/* {deleteLine.modal} */}
      {newLine.modal}
      {/* {newBuildOrder.modal} */}
      {/* {allocateBySerials.modal} */}
      {/* {allocateStock.modal} */}
      {/* {orderPartsWizard.wizard} */}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.transfer_order_line_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          enableSelection: true,
          enableDownload: true,
          params: {
            order: orderId,
            part_detail: true
          },
          //   rowActions: rowActions,
          tableActions: tableActions,
          tableFilters: tableFilters
          //   rowExpansion: rowExpansion
        }}
      />
    </>
  );
}
