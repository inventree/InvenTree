import { t } from '@lingui/macro';
import { Alert, Group, Stack, Text } from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import {
  IconArrowRight,
  IconCircleCheck,
  IconFileArrowLeft,
  IconLock,
  IconSwitch3
} from '@tabler/icons-react';
import { type ReactNode, useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { ActionButton } from '../../components/buttons/ActionButton';
import { AddItemButton } from '../../components/buttons/AddItemButton';
import { YesNoButton } from '../../components/buttons/YesNoButton';
import { Thumbnail } from '../../components/images/Thumbnail';
import ImporterDrawer from '../../components/importer/ImporterDrawer';
import { useApi } from '../../contexts/ApiContext';
import { formatDecimal, formatPriceRange } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { bomItemFields } from '../../forms/BomForms';
import { dataImporterSessionFields } from '../../forms/ImporterForms';
import { navigateToLink } from '../../functions/navigation';
import { notYetImplemented } from '../../functions/notifications';
import {
  useApiFormModal,
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
  NoteColumn,
  ReferenceColumn
} from '../ColumnRenderers';
import type { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { type RowAction, RowDeleteAction, RowEditAction } from '../RowActions';
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
  partLocked,
  params = {}
}: Readonly<{
  partId: number;
  partLocked?: boolean;
  params?: any;
}>) {
  const api = useApi();
  const user = useUserState();
  const table = useTable('bom');
  const navigate = useNavigate();

  const [importOpened, setImportOpened] = useState<boolean>(false);

  const [selectedSession, setSelectedSession] = useState<number | undefined>(
    undefined
  );

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'sub_part',
        switchable: false,
        sortable: true,
        render: (record) => {
          const part = record.sub_part_detail;
          const extra = [];

          if (record.part != partId) {
            extra.push(
              <Text key='different-parent'>{t`This BOM item is defined for a different parent`}</Text>
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
      {
        accessor: 'sub_part_detail.IPN',
        title: t`IPN`,
        sortable: true
      },
      DescriptionColumn({
        accessor: 'sub_part_detail.description'
      }),
      ReferenceColumn({
        switchable: true
      }),
      {
        accessor: 'quantity',
        switchable: false,
        sortable: true,
        render: (record: any) => {
          const quantity = formatDecimal(record.quantity);
          const units = record.sub_part_detail?.units;

          return (
            <Group justify='space-between' grow>
              <Text>{quantity}</Text>
              {record.overage && <Text size='xs'>+{record.overage}</Text>}
              {units && <Text size='xs'>{units}</Text>}
            </Group>
          );
        }
      },
      {
        accessor: 'substitutes',
        // TODO: Show hovercard with list of substitutes
        render: (row) => {
          const substitutes = row.substitutes ?? [];

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
      BooleanColumn({
        accessor: 'validated'
      }),
      {
        accessor: 'price_range',
        title: t`Unit Price`,
        ordering: 'pricing_max',
        sortable: true,
        switchable: true,
        render: (record: any) =>
          formatPriceRange(record.pricing_min, record.pricing_max)
      },
      {
        accessor: 'total_price',
        title: t`Total Price`,
        ordering: 'pricing_max_total',
        sortable: true,
        switchable: true,
        render: (record: any) =>
          formatPriceRange(record.pricing_min_total, record.pricing_max_total)
      },
      {
        accessor: 'available_stock',
        sortable: true,
        render: (record) => {
          const extra: ReactNode[] = [];

          const available_stock: number = availableStockQuantity(record);
          const on_order: number = record?.on_order ?? 0;
          const building: number = record?.building ?? 0;

          const text =
            available_stock <= 0 ? (
              <Text c='red' style={{ fontStyle: 'italic' }}>{t`No stock`}</Text>
            ) : (
              available_stock
            );

          if (record.external_stock > 0) {
            extra.push(
              <Text key='external'>
                {t`External stock`}: {record.external_stock}
              </Text>
            );
          }

          if (record.available_substitute_stock > 0) {
            extra.push(
              <Text key='substitute'>
                {t`Includes substitute stock`}:{' '}
                {record.available_substitute_stock}
              </Text>
            );
          }

          if (record.allow_variants && record.available_variant_stock > 0) {
            extra.push(
              <Text key='variant'>
                {t`Includes variant stock`}: {record.available_variant_stock}
              </Text>
            );
          }

          if (on_order > 0) {
            extra.push(
              <Text key='on_order'>
                {t`On order`}: {on_order}
              </Text>
            );
          }

          if (building > 0) {
            extra.push(
              <Text key='building'>
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
        sortable: true,
        render: (record: any) => {
          if (record.can_build === null || record.can_build === undefined) {
            return '-';
          }

          if (
            !Number.isFinite(record.can_build) ||
            Number.isNaN(record.can_build)
          ) {
            return '-';
          }

          const can_build = Math.trunc(record.can_build);
          const value = (
            <Text
              fs={record.consumable && 'italic'}
              c={can_build <= 0 && !record.consumable ? 'red' : undefined}
            >
              {can_build}
            </Text>
          );

          const extra = [];

          if (record.consumable) {
            extra.push(<Text key='consumable'>{t`Consumable item`}</Text>);
          } else if (can_build <= 0) {
            extra.push(
              <Text key='no-build' c='red'>{t`No available stock`}</Text>
            );
          }

          return (
            <TableHoverCard value={value} extra={extra} title={t`Can Build`} />
          );
        }
      },
      NoteColumn({})
    ];
  }, [partId, params]);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'sub_part_testable',
        label: t`Testable Part`,
        description: t`Show testable items`
      },
      {
        name: 'sub_part_trackable',
        label: t`Trackable Part`,
        description: t`Show trackable items`
      },
      {
        name: 'sub_part_assembly',
        label: t`Assembled Part`,
        description: t`Show assembled items`
      },
      {
        name: 'available_stock',
        label: t`Available Stock`,
        description: t`Show items with available stock`
      },
      {
        name: 'on_order',
        label: t`On Order`,
        description: t`Show items on order`
      },
      {
        name: 'validated',
        label: t`Validated`,
        description: t`Show validated items`
      },
      {
        name: 'inherited',
        label: t`Inherited`,
        description: t`Show inherited items`
      },
      {
        name: 'allow_variants',
        label: t`Allow Variants`,
        description: t`Show items which allow variant substitution`
      },
      {
        name: 'optional',
        label: t`Optional`,
        description: t`Show optional items`
      },
      {
        name: 'consumable',
        label: t`Consumable`,
        description: t`Show consumable items`
      },
      {
        name: 'has_pricing',
        label: t`Has Pricing`,
        description: t`Show items with pricing`
      }
    ];
  }, [partId, params]);

  const [selectedBomItem, setSelectedBomItem] = useState<number>(0);

  const importSessionFields = useMemo(() => {
    const fields = dataImporterSessionFields();

    fields.model_type.hidden = true;
    fields.model_type.value = 'bomitem';

    fields.field_overrides.value = {
      part: partId
    };

    return fields;
  }, [partId]);

  const importBomItem = useCreateApiFormModal({
    url: ApiEndpoints.import_session_list,
    title: t`Import BOM Data`,
    fields: importSessionFields,
    onFormSuccess: (response: any) => {
      setSelectedSession(response.pk);
      setImportOpened(true);
    }
  });

  const newBomItem = useCreateApiFormModal({
    url: ApiEndpoints.bom_list,
    title: t`Add BOM Item`,
    fields: bomItemFields(),
    initialData: {
      part: partId
    },
    successMessage: t`BOM item created`,
    table: table
  });

  const editBomItem = useEditApiFormModal({
    url: ApiEndpoints.bom_list,
    pk: selectedBomItem,
    title: t`Edit BOM Item`,
    fields: bomItemFields(),
    successMessage: t`BOM item updated`,
    table: table
  });

  const deleteBomItem = useDeleteApiFormModal({
    url: ApiEndpoints.bom_list,
    pk: selectedBomItem,
    title: t`Delete BOM Item`,
    successMessage: t`BOM item deleted`,
    table: table
  });

  const validateBom = useApiFormModal({
    url: ApiEndpoints.bom_validate,
    method: 'PUT',
    fields: {
      valid: {
        hidden: true,
        value: true
      }
    },
    title: t`Validate BOM`,
    pk: partId,
    preFormContent: (
      <Alert color='green' icon={<IconCircleCheck />} title={t`Validate BOM`}>
        <Text>{t`Do you want to validate the bill of materials for this assembly?`}</Text>
      </Alert>
    ),
    successMessage: t`BOM validated`,
    onFormSuccess: () => table.refreshTable()
  });

  const validateBomItem = useCallback((record: any) => {
    const url = apiUrl(ApiEndpoints.bom_item_validate, record.pk);

    api
      .patch(url, { valid: true })
      .then((_response) => {
        showNotification({
          title: t`Success`,
          message: t`BOM item validated`,
          color: 'green'
        });

        table.refreshTable();
      })
      .catch((_error) => {
        showNotification({
          title: t`Error`,
          message: t`Failed to validate BOM item`,
          color: 'red'
        });
      });
  }, []);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      // If this BOM item is defined for a *different* parent, then it cannot be edited
      if (record.part && record.part != partId) {
        return [
          {
            title: t`View BOM`,
            onClick: (event: any) => {
              navigateToLink(`/part/${record.part}/bom/`, navigate, event);
            },
            icon: <IconArrowRight />
          }
        ];
      }

      return [
        {
          title: t`Validate BOM Line`,
          color: 'green',
          hidden:
            partLocked ||
            record.validated ||
            !user.hasChangeRole(UserRoles.part),
          icon: <IconCircleCheck />,
          onClick: () => validateBomItem(record)
        },
        RowEditAction({
          hidden: partLocked || !user.hasChangeRole(UserRoles.part),
          onClick: () => {
            setSelectedBomItem(record.pk);
            editBomItem.open();
          }
        }),
        {
          title: t`Edit Substitutes`,
          color: 'blue',
          hidden: partLocked || !user.hasChangeRole(UserRoles.part),
          icon: <IconSwitch3 />,
          onClick: notYetImplemented
        },
        RowDeleteAction({
          hidden: partLocked || !user.hasDeleteRole(UserRoles.part),
          onClick: () => {
            setSelectedBomItem(record.pk);
            deleteBomItem.open();
          }
        })
      ];
    },
    [partId, partLocked, user]
  );

  const tableActions = useMemo(() => {
    return [
      <ActionButton
        key='import-bom'
        hidden={partLocked || !user.hasAddRole(UserRoles.part)}
        tooltip={t`Import BOM Data`}
        icon={<IconFileArrowLeft />}
        onClick={() => importBomItem.open()}
      />,
      <ActionButton
        key='validate-bom'
        hidden={partLocked || !user.hasChangeRole(UserRoles.part)}
        tooltip={t`Validate BOM`}
        icon={<IconCircleCheck />}
        onClick={() => validateBom.open()}
      />,
      <AddItemButton
        key='add-bom-item'
        hidden={partLocked || !user.hasAddRole(UserRoles.part)}
        tooltip={t`Add BOM Item`}
        onClick={() => newBomItem.open()}
      />
    ];
  }, [partLocked, user]);

  return (
    <>
      {importBomItem.modal}
      {newBomItem.modal}
      {editBomItem.modal}
      {validateBom.modal}
      {deleteBomItem.modal}
      <Stack gap='xs'>
        {partLocked && (
          <Alert
            title={t`Part is Locked`}
            color='orange'
            icon={<IconLock />}
            p='xs'
          >
            <Text>{t`Bill of materials cannot be edited, as the part is locked`}</Text>
          </Alert>
        )}
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
            tableActions: tableActions,
            tableFilters: tableFilters,
            modelType: ModelType.part,
            modelField: 'sub_part',
            rowActions: rowActions,
            enableSelection: !partLocked,
            enableBulkDelete: !partLocked && user.hasDeleteRole(UserRoles.part),
            enableDownload: true
          }}
        />
      </Stack>
      <ImporterDrawer
        sessionId={selectedSession ?? -1}
        opened={selectedSession != undefined && importOpened}
        onClose={() => {
          setSelectedSession(undefined);
          setImportOpened(false);
          table.refreshTable();
        }}
      />
    </>
  );
}
