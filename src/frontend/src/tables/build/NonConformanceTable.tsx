import { t } from '@lingui/core/macro';
import { useMemo } from 'react';

import { AddItemButton } from '@lib/components/AddItemButton';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import useTable from '@lib/hooks/UseTable';
import {
  CreationDateColumn,
  DescriptionColumn,
  PartColumn,
  ReferenceColumn,
  ResponsibleColumn,
  StatusColumn,
  TargetDateColumn
} from '../../components/tables/ColumnRenderers';
import { InvenTreeTable } from '../../components/tables/InvenTreeTable';
import { useNonConformanceFields } from '../../forms/NCRForms';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { useUserState } from '../../states/UserState';
import NonConformanceFilters from './NonConformanceFilters';

/**
 * Table of NonConformance (NCR) reports.
 *
 * When rendered against a particular record (e.g. on a detail page),
 * the table is filtered to NCRs linked to that record, and new NCRs
 * are created with the link pre-filled.
 */
export function NonConformanceTable({
  partId,
  buildOrderId,
  salesOrderId,
  purchaseOrderId,
  returnOrderId,
  stockItemId
}: Readonly<{
  partId?: number;
  buildOrderId?: number;
  salesOrderId?: number;
  purchaseOrderId?: number;
  returnOrderId?: number;
  stockItemId?: number;
}>) {
  const user = useUserState();

  const tableKey: string = useMemo(() => {
    if (stockItemId) return 'ncr-stock-item';
    if (buildOrderId) return 'ncr-build-order';
    if (salesOrderId) return 'ncr-sales-order';
    if (purchaseOrderId) return 'ncr-purchase-order';
    if (returnOrderId) return 'ncr-return-order';
    if (partId) return 'ncr-part';
    return 'ncr-index';
  }, [
    partId,
    buildOrderId,
    salesOrderId,
    purchaseOrderId,
    returnOrderId,
    stockItemId
  ]);

  const table = useTable(tableKey);

  const tableFilters = useMemo(() => NonConformanceFilters(), []);

  const tableColumns = useMemo(() => {
    return [
      ReferenceColumn({}),
      PartColumn({ hidden: !!partId }),
      DescriptionColumn({}),
      StatusColumn({ model: ModelType.nonconformance }),
      TargetDateColumn({}),
      CreationDateColumn({
        defaultVisible: false
      }),
      ResponsibleColumn({})
    ];
  }, [partId]);

  const ncrFields = useNonConformanceFields({ partId });

  const newNcr = useCreateApiFormModal({
    url: ApiEndpoints.ncr_list,
    title: t`Report Non-Conformance`,
    fields: ncrFields,
    initialData: {
      part: partId,
      build_order: buildOrderId,
      sales_order: salesOrderId,
      purchase_order: purchaseOrderId,
      return_order: returnOrderId
    },
    follow: true,
    modelType: ModelType.nonconformance
  });

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add-ncr'
        tooltip={t`Report Non-Conformance`}
        onClick={() => newNcr.open()}
        hidden={!user.hasAddRole(UserRoles.ncr)}
      />
    ];
  }, [user]);

  return (
    <>
      {newNcr.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.ncr_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          params: {
            part: partId,
            build_order: buildOrderId,
            sales_order: salesOrderId,
            purchase_order: purchaseOrderId,
            return_order: returnOrderId,
            stock_item: stockItemId,
            part_detail: true
          },
          tableFilters: tableFilters,
          tableActions: tableActions,
          modelType: ModelType.nonconformance,
          enableSelection: true,
          enableReports: true,
          enableDownload: true
        }}
      />
    </>
  );
}
