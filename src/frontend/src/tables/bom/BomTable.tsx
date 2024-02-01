import { t } from '@lingui/macro';
import { Text } from '@mantine/core';
import {
  IconArrowRight,
  IconCircleCheck,
  IconSwitch3
} from '@tabler/icons-react';
import { ReactNode, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { Thumbnail } from '../../components/images/Thumbnail';
import { YesNoButton } from '../../components/items/YesNoButton';
import { formatPriceRange } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { bomItemFields } from '../../forms/BomForms';
import { openDeleteApiForm, openEditApiForm } from '../../functions/forms';
import { getDetailUrl } from '../../functions/urls';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import {
  BooleanColumn,
  DescriptionColumn,
  NoteColumn
} from '../ColumnRenderers';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowAction, RowDeleteAction, RowEditAction } from '../RowActions';
import { TableHoverCard } from '../TableHoverCard';

// Calculate the total stock quantity available for a given BomItem
function availableStockQuantity(record: any): number {
  // Base availability
  let available: number = record.available_stock;

  // Add in available substitute stock
  available += record?.available_substitute_stock ?? 0;

  // Add in variant stock
  if (record.allow_variants) {
    available += record?.available_variant_stock ?? 0;
  }

  return available;
}

export function BomTable({
  partId,
  params = {}
}: {
  partId: number;
  params?: any;
}) {
  const navigate = useNavigate();

  const user = useUserState();

  const table = useTable('bom');

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'part',
        switchable: false,
        sortable: true,
        render: (record) => {
          let part = record.sub_part_detail;
          let extra = [];

          if (record.part != partId) {
            extra.push(
              <Text key="different-parent">{t`This BOM item is defined for a different parent`}</Text>
            );
          }

          return (
            part && (
              <TableHoverCard
                value={
                  <Thumbnail
                    src={part.thumbnail || part.image}
                    alt={part.description}
                    text={part.full_name}
                  />
                }
                extra={extra}
                title={t`Part Information`}
              />
            )
          );
        }
      },
      DescriptionColumn({
        accessor: 'sub_part_detail.description'
      }),
      {
        accessor: 'reference'
      },
      {
        accessor: 'quantity',
        switchable: false,
        sortable: true
        // TODO: Custom quantity renderer
        // TODO: see bom.js for existing implementation
      },
      {
        accessor: 'substitutes',
        // TODO: Show hovercard with list of substitutes
        render: (row) => {
          let substitutes = row.substitutes ?? [];

          return substitutes.length > 0 ? (
            row.length
          ) : (
            <YesNoButton value={false} />
          );
        }
      },
      BooleanColumn({
        accessor: 'optional'
      }),
      BooleanColumn({
        accessor: 'consumable'
      }),
      BooleanColumn({
        accessor: 'allow_variants'
      }),
      BooleanColumn({
        accessor: 'inherited'
        // TODO: Custom renderer for this column
        // TODO: See bom.js for existing implementation
      }),
      {
        accessor: 'price_range',
        title: t`Price Range`,

        sortable: false,
        render: (record: any) =>
          formatPriceRange(record.pricing_min, record.pricing_max)
      },
      {
        accessor: 'available_stock',

        render: (record) => {
          let extra: ReactNode[] = [];

          let available_stock: number = availableStockQuantity(record);
          let on_order: number = record?.on_order ?? 0;
          let building: number = record?.building ?? 0;

          let text =
            available_stock <= 0 ? (
              <Text color="red" italic>{t`No stock`}</Text>
            ) : (
              available_stock
            );

          if (record.available_substitute_stock > 0) {
            extra.push(
              <Text key="substitute">
                {t`Includes substitute stock`}:{' '}
                {record.available_substitute_stock}
              </Text>
            );
          }

          if (record.allow_variants && record.available_variant_stock > 0) {
            extra.push(
              <Text key="variant">
                {t`Includes variant stock`}: {record.available_variant_stock}
              </Text>
            );
          }

          if (on_order > 0) {
            extra.push(
              <Text key="on_order">
                {t`On order`}: {on_order}
              </Text>
            );
          }

          if (building > 0) {
            extra.push(
              <Text key="building">
                {t`Building`}: {building}
              </Text>
            );
          }

          return (
            <TableHoverCard
              value={text}
              extra={extra}
              title={t`Stock Information`}
            />
          );
        }
      },
      {
        accessor: 'can_build',
        title: t`Can Build`,
        sortable: false, // TODO: Custom sorting via API
        render: (record: any) => {
          if (record.consumable) {
            return <Text italic>{t`Consumable item`}</Text>;
          }

          let can_build = availableStockQuantity(record) / record.quantity;
          can_build = Math.trunc(can_build);

          return (
            <Text color={can_build <= 0 ? 'red' : undefined}>{can_build}</Text>
          );
        }
      },
      NoteColumn()
    ];
  }, [partId, params]);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'sub_part_trackable',
        label: t`Trackable Part`,
        description: t`Show trackable items`
      },
      {
        name: 'sub_part_assembly',
        label: t`Assembled Part`,
        description: t`Show asssmbled items`
      },
      {
        name: 'available_stock',
        description: t`Show items with available stock`
      },
      {
        name: 'on_order',
        description: t`Show items on order`
      },
      {
        name: 'validated',
        description: t`Show validated items`
      },
      {
        name: 'inherited',
        description: t`Show inherited items`
      },
      {
        name: 'optional',
        description: t`Show optional items`
      },
      {
        name: 'consumable',
        description: t`Show consumable items`
      },
      {
        name: 'has_pricing',
        label: t`Has Pricing`,
        description: t`Show items with pricing`
      }
    ];
  }, [partId, params]);

  const rowActions = useCallback(
    (record: any) => {
      // If this BOM item is defined for a *different* parent, then it cannot be edited
      if (record.part && record.part != partId) {
        return [
          {
            title: t`View BOM`,
            onClick: () => navigate(`/part/${record.part}/`),
            icon: <IconArrowRight />
          }
        ];
      }

      let actions: RowAction[] = [];

      // TODO: Enable BomItem validation
      actions.push({
        title: t`Validate BOM line`,
        color: 'green',
        hidden: record.validated || !user.hasChangeRole(UserRoles.part),
        icon: <IconCircleCheck />
      });

      // TODO: Enable editing of substitutes
      actions.push({
        title: t`Edit Substitutes`,
        color: 'blue',
        hidden: !user.hasChangeRole(UserRoles.part),
        icon: <IconSwitch3 />
      });

      // Action on edit
      actions.push(
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.part),
          onClick: () => {
            openEditApiForm({
              url: ApiEndpoints.bom_list,
              pk: record.pk,
              title: t`Edit Bom Item`,
              fields: bomItemFields(),
              successMessage: t`Bom item updated`,
              onFormSuccess: table.refreshTable
            });
          }
        })
      );

      // Action on delete
      actions.push(
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.part),
          onClick: () => {
            openDeleteApiForm({
              url: ApiEndpoints.bom_list,
              pk: record.pk,
              title: t`Delete Bom Item`,
              successMessage: t`Bom item deleted`,
              onFormSuccess: table.refreshTable,
              preFormWarning: t`Are you sure you want to remove this BOM item?`
            });
          }
        })
      );

      return actions;
    },
    [partId, user]
  );

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.bom_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        params: {
          ...params,
          part: partId,
          part_detail: true,
          sub_part_detail: true
        },
        tableFilters: tableFilters,
        onRowClick: (row) =>
          navigate(getDetailUrl(ModelType.part, row.sub_part)),
        rowActions: rowActions
      }}
    />
  );
}
