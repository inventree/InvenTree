import { t } from '@lingui/macro';
import { ActionIcon, Stack, Text, Tooltip } from '@mantine/core';
import { IconCirclePlus } from '@tabler/icons-react';
import { ReactNode, useCallback, useMemo } from 'react';

import { supplierPartFields } from '../../../forms/CompanyForms';
import {
  openCreateApiForm,
  openDeleteApiForm,
  openEditApiForm
} from '../../../functions/forms';
import { useTableRefresh } from '../../../hooks/TableRefresh';
import { ApiPaths, apiUrl } from '../../../states/ApiState';
import { useUserState } from '../../../states/UserState';
import { AddItemButton } from '../../buttons/AddItemButton';
import { Thumbnail } from '../../images/Thumbnail';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowDeleteAction, RowEditAction } from '../RowActions';
import { TableHoverCard } from '../TableHoverCard';

/*
 * Construct a table listing supplier parts
 */

export function SupplierPartTable({ params }: { params: any }): ReactNode {
  const { tableKey, refreshTable } = useTableRefresh('supplierparts');

  const user = useUserState();

  // Construct table columns for this table
  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'part',
        title: t`Part`,
        switchable: 'part' in params,
        sortable: true,
        render: (record: any) => {
          let part = record?.part_detail ?? {};

          return (
            <Thumbnail src={part?.thumbnail ?? part.image} text={part.name} />
          );
        }
      },
      {
        accessor: 'supplier',
        title: t`Supplier`,
        sortable: true,
        render: (record: any) => {
          let supplier = record?.supplier_detail ?? {};

          return (
            <Thumbnail
              src={supplier?.thumbnail ?? supplier.image}
              text={supplier.name}
            />
          );
        }
      },
      {
        accessor: 'SKU',
        title: t`Supplier Part`,
        sortable: true
      },
      {
        accessor: 'description',
        title: t`Description`,
        sortable: false,
        switchable: true
      },
      {
        accessor: 'manufacturer',
        switchable: true,
        sortable: true,
        title: t`Manufacturer`,
        render: (record: any) => {
          let manufacturer = record?.manufacturer_detail ?? {};

          return (
            <Thumbnail
              src={manufacturer?.thumbnail ?? manufacturer.image}
              text={manufacturer.name}
            />
          );
        }
      },
      {
        accessor: 'MPN',
        switchable: true,
        sortable: true,
        title: t`MPN`,
        render: (record: any) => record?.manufacturer_part_detail?.MPN
      },
      {
        accessor: 'in_stock',
        title: t`In Stock`,
        sortable: true,
        switchable: true
      },
      {
        accessor: 'packaging',
        title: t`Packaging`,
        sortable: true,
        switchable: true
      },
      {
        accessor: 'pack_quantity',
        title: t`Pack Quantity`,
        sortable: true,
        switchable: true,
        render: (record: any) => {
          let part = record?.part_detail ?? {};

          let extra = [];

          if (part.units) {
            extra.push(
              <Text>
                {t`Base units`} : {part.units}
              </Text>
            );
          }

          return (
            <TableHoverCard
              value={record.pack_quantity}
              extra={extra.length > 0 && <Stack spacing="xs">{extra}</Stack>}
              title={t`Pack Quantity`}
            />
          );
        }
      },
      {
        accessor: 'link',
        title: t`Link`,
        sortable: false,
        switchable: true
        // TODO: custom link renderer?
      },
      {
        accessor: 'note',
        title: t`Notes`,
        sortable: false,
        switchable: true
      },
      {
        accessor: 'available',
        title: t`Availability`,
        sortable: true,
        switchable: true,
        render: (record: any) => {
          let extra = [];

          if (record.availablility_updated) {
            extra.push(
              <Text>
                {t`Updated`} : {record.availablility_updated}
              </Text>
            );
          }

          return (
            <TableHoverCard
              value={record.available}
              extra={extra.length > 0 && <Stack spacing="xs">{extra}</Stack>}
            />
          );
        }
      }
    ];
  }, [params]);

  const addSupplierPart = useCallback(() => {
    let fields = supplierPartFields();

    fields.part.value = params?.part;
    fields.supplier.value = params?.supplier;

    openCreateApiForm({
      url: ApiPaths.supplier_part_list,
      title: t`Add Supplier Part`,
      fields: fields,
      onFormSuccess: refreshTable,
      successMessage: t`Supplier part created`
    });
  }, [params]);

  // Table actions
  const tableActions = useMemo(() => {
    // TODO: Hide actions based on user permissions

    return [
      <AddItemButton tooltip={t`Add supplier part`} onClick={addSupplierPart} />
    ];
  }, [user]);

  // Row action callback
  const rowActions = useCallback(
    (record: any) => {
      // TODO: Adjust actions based on user permissions
      return [
        RowEditAction({
          onClick: () => {
            record.pk &&
              openEditApiForm({
                url: ApiPaths.supplier_part_list,
                pk: record.pk,
                title: t`Edit Supplier Part`,
                fields: supplierPartFields(),
                onFormSuccess: refreshTable,
                successMessage: t`Supplier part updated`
              });
          }
        }),
        RowDeleteAction({
          onClick: () => {
            record.pk &&
              openDeleteApiForm({
                url: ApiPaths.supplier_part_list,
                pk: record.pk,
                title: t`Delete Supplier Part`,
                successMessage: t`Supplier part deleted`,
                onFormSuccess: refreshTable,
                preFormContent: (
                  <Text>{t`Are you sure you want to remove this supplier part?`}</Text>
                )
              });
          }
        })
      ];
    },
    [user]
  );

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.supplier_part_list)}
      tableKey={tableKey}
      columns={tableColumns}
      props={{
        params: {
          ...params,
          part_detail: true,
          supplier_detail: true,
          manufacturer_detail: true
        },
        rowActions: rowActions,
        customActionGroups: tableActions
      }}
    />
  );
}
