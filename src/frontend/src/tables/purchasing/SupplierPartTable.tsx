import { t } from '@lingui/macro';
import { Text } from '@mantine/core';
import { type ReactNode, useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { Thumbnail } from '../../components/images/Thumbnail';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { useSupplierPartFields } from '../../forms/CompanyForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import type { TableColumn } from '../Column';
import {
  BooleanColumn,
  DescriptionColumn,
  LinkColumn,
  NoteColumn,
  PartColumn
} from '../ColumnRenderers';
import type { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { type RowAction, RowDeleteAction, RowEditAction } from '../RowActions';
import { TableHoverCard } from '../TableHoverCard';

/*
 * Construct a table listing supplier parts
 */

export function SupplierPartTable({
  params
}: Readonly<{ params: any }>): ReactNode {
  const table = useTable('supplierparts');

  const user = useUserState();

  // Construct table columns for this table
  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'part',
        switchable: 'part' in params,
        sortable: true,
        render: (record: any) =>
          PartColumn({ part: record?.part_detail, full_name: true })
      },
      {
        accessor: 'supplier',
        sortable: true,
        render: (record: any) => {
          const supplier = record?.supplier_detail ?? {};

          return supplier?.pk ? (
            <Thumbnail
              src={supplier?.thumbnail ?? supplier.image}
              text={supplier.name}
            />
          ) : (
            '-'
          );
        }
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
        render: (record: any) => {
          const manufacturer = record?.manufacturer_detail ?? {};

          return manufacturer?.pk ? (
            <Thumbnail
              src={manufacturer?.thumbnail ?? manufacturer.image}
              text={manufacturer.name}
            />
          ) : (
            '-'
          );
        }
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
        switchable: true
      }),
      {
        accessor: 'in_stock',
        sortable: true
      },
      {
        accessor: 'packaging',
        sortable: true
      },
      {
        accessor: 'pack_quantity',
        sortable: true,

        render: (record: any) => {
          const part = record?.part_detail ?? {};

          const extra = [];

          if (part.units) {
            extra.push(
              <Text key='base'>
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
  }, [params]);

  const supplierPartFields = useSupplierPartFields({
    partId: params?.part
  });

  const addSupplierPart = useCreateApiFormModal({
    url: ApiEndpoints.supplier_part_list,
    title: t`Add Supplier Part`,
    fields: supplierPartFields,
    initialData: {
      part: params?.part,
      supplier: params?.supplier
    },
    table: table,
    successMessage: t`Supplier part created`
  });

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add-supplier-part'
        tooltip={t`Add supplier part`}
        onClick={() => addSupplierPart.open()}
        hidden={!user.hasAddRole(UserRoles.purchase_order)}
      />
    ];
  }, [user]);

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

  const [selectedSupplierPart, setSelectedSupplierPart] = useState<number>(0);

  const editSupplierPart = useEditApiFormModal({
    url: ApiEndpoints.supplier_part_list,
    pk: selectedSupplierPart,
    title: t`Edit Supplier Part`,
    fields: editSupplierPartFields,
    table: table
  });

  const deleteSupplierPart = useDeleteApiFormModal({
    url: ApiEndpoints.supplier_part_list,
    pk: selectedSupplierPart,
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
            setSelectedSupplierPart(record.pk);
            editSupplierPart.open();
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.purchase_order),
          onClick: () => {
            setSelectedSupplierPart(record.pk);
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
      {deleteSupplierPart.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.supplier_part_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          params: {
            ...params,
            part_detail: true,
            supplier_detail: true,
            manufacturer_detail: true
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
