import { t } from '@lingui/core/macro';
import { Text } from '@mantine/core';
import { type ReactNode, useCallback, useMemo, useState } from 'react';

import { ActionButton } from '@lib/components/ActionButton';
import { AddItemButton } from '@lib/components/AddItemButton';
import {
  type RowAction,
  RowDeleteAction,
  RowDuplicateAction,
  RowEditAction
} from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { IconPackageImport } from '@tabler/icons-react';
import ImportPartWizard from '../../components/wizards/ImportPartWizard';
import { useSupplierPartFields } from '../../forms/CompanyForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { usePluginsWithMixin } from '../../hooks/UsePlugins';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import {
  BooleanColumn,
  CompanyColumn,
  DecimalColumn,
  DescriptionColumn,
  LinkColumn,
  NoteColumn,
  PartColumn
} from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import { TableHoverCard } from '../TableHoverCard';

/*
 * Construct a table listing supplier parts
 */

export function SupplierPartTable({
  manufacturerId,
  manufacturerPartId,
  partId,
  supplierId
}: Readonly<{
  manufacturerId?: number;
  manufacturerPartId?: number;
  partId?: number;
  supplierId?: number;
}>): ReactNode {
  const table = useTable('supplierparts');

  const user = useUserState();

  // Construct table columns for this table
  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      PartColumn({
        switchable: !!partId,
        part: 'part_detail'
      }),
      {
        accessor: 'part_detail.IPN',
        title: t`IPN`,
        sortable: true,
        ordering: 'IPN',
        switchable: true
      },
      {
        accessor: 'supplier',
        sortable: true,
        render: (record: any) => (
          <CompanyColumn company={record?.supplier_detail} />
        )
      },
      {
        accessor: 'SKU',
        title: t`Supplier Part`,
        sortable: true
      },
      DescriptionColumn({}),
      {
        accessor: 'manufacturer',
        title: t`Manufacturer`,
        sortable: true,
        render: (record: any) => (
          <CompanyColumn company={record?.manufacturer_detail} />
        )
      },
      {
        accessor: 'MPN',
        sortable: true,
        title: t`MPN`,
        render: (record: any) => record?.manufacturer_part_detail?.MPN
      },
      BooleanColumn({
        accessor: 'active',
        title: t`Active`,
        sortable: true,
        switchable: true,
        defaultVisible: false
      }),
      DecimalColumn({
        accessor: 'in_stock',
        sortable: true
      }),
      {
        accessor: 'packaging',
        sortable: true,
        defaultVisible: false
      },
      {
        accessor: 'pack_quantity',
        sortable: true,
        render: (record: any) => {
          const part = record?.part_detail ?? {};

          const extra = [];

          if (part.units) {
            extra.push(
              <Text key='base' size='sm'>
                {t`Base units`} : {part.units}
              </Text>
            );
          }

          return (
            <TableHoverCard
              value={record.pack_quantity}
              extra={extra}
              title={t`Pack Quantity`}
            />
          );
        }
      },
      LinkColumn({}),
      NoteColumn({}),
      {
        accessor: 'available',
        sortable: true,
        defaultVisible: false,
        render: (record: any) => {
          const extra = [];

          if (record.availablility_updated) {
            extra.push(
              <Text>
                {t`Updated`} : {record.availablility_updated}
              </Text>
            );
          }

          return <TableHoverCard value={record.available} extra={extra} />;
        }
      }
    ];
  }, [partId]);

  const supplierPartFields = useSupplierPartFields({
    partId: partId
  });

  const addSupplierPart = useCreateApiFormModal({
    url: ApiEndpoints.supplier_part_list,
    title: t`Add Supplier Part`,
    fields: supplierPartFields,
    initialData: {
      part: partId,
      supplier: supplierId,
      manufacturer_part: manufacturerPartId
    },
    table: table,
    successMessage: t`Supplier part created`
  });

  const supplierPlugins = usePluginsWithMixin('supplier');
  const importPartWizard = ImportPartWizard({
    partId: partId
  });

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add-supplier-part'
        tooltip={t`Add supplier part`}
        onClick={() => addSupplierPart.open()}
        hidden={!user.hasAddRole(UserRoles.purchase_order)}
      />,
      <ActionButton
        key='import-part'
        icon={<IconPackageImport />}
        color='green'
        tooltip={t`Import supplier part`}
        onClick={() => importPartWizard.openWizard()}
        hidden={
          supplierPlugins.length === 0 ||
          !user.hasAddRole(UserRoles.part) ||
          !partId
        }
      />
    ];
  }, [user, partId, supplierPlugins]);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'active',
        label: t`Active`,
        description: t`Show active supplier parts`
      },
      {
        name: 'part_active',
        label: t`Active Part`,
        description: t`Show active internal parts`
      },
      {
        name: 'supplier_active',
        label: t`Active Supplier`,
        description: t`Show active suppliers`
      },
      {
        name: 'has_stock',
        label: t`In Stock`,
        description: t`Show supplier parts with stock`
      }
    ];
  }, []);

  const editSupplierPartFields = useSupplierPartFields({});

  const [selectedSupplierPart, setSelectedSupplierPart] =
    useState<any>(undefined);

  const editSupplierPart = useEditApiFormModal({
    url: ApiEndpoints.supplier_part_list,
    pk: selectedSupplierPart?.pk,
    title: t`Edit Supplier Part`,
    fields: useMemo(() => editSupplierPartFields, [editSupplierPartFields]),
    table: table
  });

  const duplicateSupplierPart = useCreateApiFormModal({
    url: ApiEndpoints.supplier_part_list,
    title: t`Add Supplier Part`,
    fields: useMemo(() => editSupplierPartFields, [editSupplierPartFields]),
    initialData: {
      ...selectedSupplierPart,
      active: true
    },
    table: table,
    successMessage: t`Supplier part created`
  });

  const deleteSupplierPart = useDeleteApiFormModal({
    url: ApiEndpoints.supplier_part_list,
    pk: selectedSupplierPart?.pk,
    title: t`Delete Supplier Part`,
    table: table
  });

  // Row action callback
  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.purchase_order),
          onClick: () => {
            setSelectedSupplierPart(record);
            editSupplierPart.open();
          }
        }),
        RowDuplicateAction({
          hidden: !user.hasAddRole(UserRoles.purchase_order),
          onClick: () => {
            setSelectedSupplierPart(record);
            duplicateSupplierPart.open();
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.purchase_order),
          onClick: () => {
            setSelectedSupplierPart(record);
            deleteSupplierPart.open();
          }
        })
      ];
    },
    [user, editSupplierPartFields]
  );

  return (
    <>
      {addSupplierPart.modal}
      {editSupplierPart.modal}
      {duplicateSupplierPart.modal}
      {deleteSupplierPart.modal}
      {importPartWizard.wizard}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.supplier_part_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          params: {
            manufacturer: manufacturerId,
            manufacturer_part: manufacturerPartId,
            supplier: supplierId,
            part: partId,
            part_detail: true,
            supplier_detail: true,
            manufacturer_detail: true,
            manufacturer_part_detail: true
          },
          rowActions: rowActions,
          enableDownload: true,
          tableActions: tableActions,
          tableFilters: tableFilters,
          modelType: ModelType.supplierpart
        }}
      />
    </>
  );
}
