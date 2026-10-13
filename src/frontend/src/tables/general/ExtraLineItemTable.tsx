import { t } from '@lingui/core/macro';
import { useCallback, useMemo, useState } from 'react';

import {
  type RowAction,
  RowDeleteAction,
  RowDuplicateAction,
  RowEditAction
} from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import type { ModelType } from '@lib/enums/ModelType';
import type { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import useTable from '@lib/hooks/UseTable';
import type { TableColumn } from '@lib/types/Tables';
import { LineItemCreationMenu } from '../../components/items/LineItemCreationMenu';
import {
  DecimalColumn,
  DescriptionColumn,
  LineItemColumn,
  LinkColumn,
  NoteColumn,
  PercentageColumn,
  ProjectCodeColumn
} from '../../components/tables/ColumnRenderers';
import { InvenTreeTable } from '../../components/tables/InvenTreeTable';
import { formatCurrency } from '../../defaults/formatters';
import { extraLineItemFields } from '../../forms/CommonForms';
import { dataImporterSessionFields } from '../../forms/ImporterForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useImporterState } from '../../states/ImporterState';
import { useUserState } from '../../states/UserState';

export default function ExtraLineItemTable({
  endpoint,
  importModelType,
  orderId,
  orderDetailRefresh,
  currency,
  editable,
  role
}: Readonly<{
  endpoint: ApiEndpoints;
  importModelType: ModelType | string;
  orderId: number;
  editable: boolean;
  orderDetailRefresh: () => void;
  currency: string;
  role: UserRoles;
}>) {
  const table = useTable('extra-line-item');
  const user = useUserState();
  const openImporter = useImporterState((state) => state.openImporter);

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      LineItemColumn({}),
      {
        accessor: 'reference',
        switchable: false
      },
      DescriptionColumn({}),
      DecimalColumn({
        accessor: 'quantity',
        switchable: false
      }),
      {
        accessor: 'price',
        title: t`Unit Price`,
        render: (record: any) =>
          formatCurrency(record.price, {
            currency: record.price_currency
          })
      },
      PercentageColumn({
        accessor: 'discount',
        title: t`Discount`,
        defaultVisible: false
      }),
      {
        accessor: 'total_price',
        title: t`Total Price`,
        render: (record: any) =>
          formatCurrency(record.total_price, {
            currency: record.price_currency
          })
      },
      ProjectCodeColumn({}),
      NoteColumn({
        accessor: 'notes'
      }),
      LinkColumn({
        accessor: 'link'
      })
    ];
  }, []);

  const [initialData, setInitialData] = useState<any>({});

  const [selectedLine, setSelectedLine] = useState<number>(0);

  const newLineItem = useCreateApiFormModal({
    url: endpoint,
    title: t`Add Line Item`,
    fields: extraLineItemFields(),
    initialData: {
      ...initialData,
      price_currency: currency
    },
    onFormSuccess: orderDetailRefresh,
    table: table
  });

  const editLineItem = useEditApiFormModal({
    url: endpoint,
    pk: selectedLine,
    title: t`Edit Line Item`,
    fields: extraLineItemFields(),
    onFormSuccess: orderDetailRefresh,
    table: table
  });

  const deleteLineItem = useDeleteApiFormModal({
    url: endpoint,
    pk: selectedLine,
    title: t`Delete Line Item`,
    onFormSuccess: orderDetailRefresh,
    table: table
  });

  const importSessionFields = useMemo(() => {
    const fields = dataImporterSessionFields({ modelType: importModelType });

    fields.field_overrides.value = {
      order: orderId
    };

    fields.field_defaults.value = {
      price_currency: currency
    };

    return fields;
  }, [orderId, currency, importModelType]);

  const importLineItems = useCreateApiFormModal({
    url: ApiEndpoints.import_session_list,
    title: t`Import Line Items`,
    fields: importSessionFields,
    onFormSuccess: (response: any) => {
      openImporter(response.pk, {
        onClose: table.refreshTable
      });
    }
  });

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        RowEditAction({
          hidden: !editable || !user.hasChangeRole(role),
          onClick: () => {
            setSelectedLine(record.pk);
            editLineItem.open();
          }
        }),
        RowDuplicateAction({
          hidden: !editable || !user.hasAddRole(role),
          onClick: () => {
            setInitialData({ ...record });
            newLineItem.open();
          }
        }),
        RowDeleteAction({
          hidden: !editable || !user.hasDeleteRole(role),
          onClick: () => {
            setSelectedLine(record.pk);
            deleteLineItem.open();
          }
        })
      ];
    },
    [editable, user, role]
  );

  const tableActions = useMemo(() => {
    return [
      <LineItemCreationMenu
        key='add-line-item-actions'
        tooltip={t`Add Extra Line Item`}
        addLabel={t`Add Extra Line Item`}
        importLabel={t`Import Line Items`}
        hidden={!editable || !user.hasAddRole(role)}
        onAdd={() => {
          setInitialData({
            order: orderId
          });
          newLineItem.open();
        }}
        onImport={() => importLineItems.open()}
      />
    ];
  }, [editable, user, role, orderId, importLineItems]);

  return (
    <>
      {newLineItem.modal}
      {editLineItem.modal}
      {deleteLineItem.modal}
      {importLineItems.modal}
      <InvenTreeTable
        tableState={table}
        url={apiUrl(endpoint)}
        columns={tableColumns}
        props={{
          params: {
            order: orderId
          },
          enableSelection: true,
          enableBulkDelete: editable && user.hasDeleteRole(role),
          afterBulkDelete: orderDetailRefresh,
          defaultSortColumn: 'line',
          rowActions: rowActions,
          tableActions: tableActions
        }}
      />
    </>
  );
}
