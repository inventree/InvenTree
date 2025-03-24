import { t } from '@lingui/macro';
import { useCallback, useMemo, useState } from 'react';

import { RenderUser } from '@lib/components';
import { AddItemButton } from '@lib/components/buttons/AddItemButton';
import type { ApiFormFieldSet } from '@lib/forms';
import { useCreateApiFormModal, useDeleteApiFormModal } from '@lib/forms';
import { apiUrl } from '@lib/functions';
import { useTable } from '@lib/hooks';
import { ApiEndpoints } from '@lib/index';
import type { RowAction, TableColumn } from '@lib/tables';
import { RowDeleteAction } from '@lib/tables';
import { InvenTreeTable } from '../../../lib/tables/InvenTreeTable';
import { AttachmentLink } from '../../components/items/AttachmentLink';
import { generateStocktakeReportFields } from '../../forms/PartForms';
import { DateColumn } from '../ColumnRenderers';

export default function StocktakeReportTable() {
  const table = useTable('stocktake-report');

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'report',
        title: t`Report`,
        sortable: false,
        switchable: false,
        render: (record: any) => <AttachmentLink attachment={record.report} />,
        noContext: true
      },
      {
        accessor: 'part_count',
        title: t`Part Count`,
        sortable: false
      },
      DateColumn({
        accessor: 'date',
        title: t`Date`
      }),
      {
        accessor: 'user',
        title: t`User`,
        sortable: false,
        render: (record: any) => RenderUser({ instance: record.user_detail })
      }
    ];
  }, []);

  const [selectedReport, setSelectedReport] = useState<number | undefined>(
    undefined
  );

  const deleteReport = useDeleteApiFormModal({
    url: ApiEndpoints.part_stocktake_report_list,
    pk: selectedReport,
    title: t`Delete Report`,
    onFormSuccess: () => table.refreshTable()
  });

  const generateFields: ApiFormFieldSet = useMemo(
    () => generateStocktakeReportFields(),
    []
  );

  const generateReport = useCreateApiFormModal({
    url: ApiEndpoints.part_stocktake_report_generate,
    title: t`Generate Stocktake Report`,
    fields: generateFields,
    successMessage: t`Stocktake report scheduled`
  });

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        tooltip={t`New Stocktake Report`}
        onClick={() => generateReport.open()}
      />
    ];
  }, []);

  const rowActions = useCallback((record: any): RowAction[] => {
    return [
      RowDeleteAction({
        onClick: () => {
          setSelectedReport(record.pk);
          deleteReport.open();
        }
      })
    ];
  }, []);

  return (
    <>
      {generateReport.modal}
      {deleteReport.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.part_stocktake_report_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          enableSearch: false,
          rowActions: rowActions,
          tableActions: tableActions
        }}
      />
    </>
  );
}
