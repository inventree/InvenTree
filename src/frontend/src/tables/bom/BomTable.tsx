import {
  type RowAction,
  RowDeleteAction,
  RowEditAction
} from '@lib/components/RowActions';
import { YesNoButton } from '@lib/components/YesNoButton';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import { navigateToLink } from '@lib/functions/Navigation';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { t } from '@lingui/core/macro';
import { ActionIcon, Alert, Group, Stack, Text, Tooltip } from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import {
  IconArrowRight,
  IconCircleCheck,
  IconExclamationCircle,
  IconFileUpload,
  IconLock,
  IconPlus,
  IconSwitch3
} from '@tabler/icons-react';
import { type ReactNode, useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Thumbnail } from '../../components/images/Thumbnail';
import ImporterDrawer from '../../components/importer/ImporterDrawer';
import { ActionDropdown } from '../../components/items/ActionDropdown';
import { RenderPart } from '../../components/render/Part';
import { useApi } from '../../contexts/ApiContext';
import { formatDecimal, formatPriceRange } from '../../defaults/formatters';
import { bomItemFields, useEditBomSubstitutesForm } from '../../forms/BomForms';
import { dataImporterSessionFields } from '../../forms/ImporterForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import {
  BooleanColumn,
  CategoryColumn,
  DescriptionColumn,
  NoteColumn,
  ReferenceColumn
} from '../ColumnRenderers';
import { PartCategoryFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
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
        render: (record: any) => {
          const part = record.sub_part_detail;
          const extra = [];

          if (record.part != partId) {
            extra.push(
              <Text key='different-parent'>{t`This BOM item is defined for a different parent`}</Text>
            );
          }

          return (
            part && (
              <Group gap='xs' justify='space-between' wrap='nowrap'>
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
                {!record.validated && (
                  <Tooltip label={t`This BOM item has not been validated`}>
                    <ActionIcon color='red' variant='transparent' size='sm'>
                      <IconExclamationCircle />
                    </ActionIcon>
                  </Tooltip>
                )}
              </Group>
            )
          );
        }
      },
      {
        accessor: 'sub_part_detail.IPN',
        title: t`IPN`,
        sortable: true,
        ordering: 'IPN'
      },
      CategoryColumn({
        accessor: 'category_detail',
        defaultVisible: false,
        switchable: true,
        sortable: true,
        ordering: 'category'
      }),
      DescriptionColumn({
        accessor: 'sub_part_detail.description'
      }),
      BooleanColumn({
        accessor: 'sub_part_detail.virtual',
        defaultVisible: false,
        title: t`Virtual Part`
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
            <Group justify='space-between'>
              <Group gap='xs'>
                <Text>{quantity}</Text>
                {record.setup_quantity && record.setup_quantity > 0 && (
                  <Text size='xs'>{`(+${record.setup_quantity})`}</Text>
                )}
                {record.attrition && record.attrition > 0 && (
                  <Text size='xs'>{`(+${record.attrition}%)`}</Text>
                )}
              </Group>
              {units && <Text size='xs'>[{units}]</Text>}
            </Group>
          );
        }
      },
      {
        accessor: 'setup_quantity',
        defaultVisible: false,
        sortable: true,
        render: (record: any) => {
          const setup_quantity = record.setup_quantity;
          const units = record.sub_part_detail?.units;
          if (setup_quantity == null || setup_quantity === 0) {
            return '-';
          } else {
            return (
              <Group gap='xs' justify='space-between'>
                <Text size='xs'>{formatDecimal(setup_quantity)}</Text>
                {units && <Text size='xs'>[{units}]</Text>}
              </Group>
            );
          }
        }
      },
      {
        accessor: 'attrition',
        defaultVisible: false,
        sortable: true,
        render: (record: any) => {
          const attrition = record.attrition;
          if (attrition == null || attrition === 0) {
            return '-';
          } else {
            return <Text size='xs'>{`${formatDecimal(attrition)}%`}</Text>;
          }
        }
      },
      {
        accessor: 'rounding_multiple',
        defaultVisible: false,
        sortable: false,
        render: (record: any) => {
          const units = record.sub_part_detail?.units;
          const multiple: number | null = record.round_up_multiple;

          if (multiple == null) {
            return '-';
          } else {
            return (
              <Group gap='xs' justify='space-between'>
                <Text>{formatDecimal(multiple)}</Text>
                {units && <Text size='xs'>[{units}]</Text>}
              </Group>
            );
          }
        }
      },
      {
        accessor: 'substitutes',
        defaultVisible: false,
        render: (row: any) => {
          const substitutes = row.substitutes ?? [];

          return substitutes.length > 0 ? (
            <TableHoverCard
              value={<Text>{substitutes.length}</Text>}
              title={t`Substitutes`}
              extra={substitutes.map((sub: any) => (
                <RenderPart instance={sub.part_detail} />
              ))}
            />
          ) : (
            <YesNoButton value={false} />
          );
        }
      },
      BooleanColumn({
        accessor: 'optional',
        defaultVisible: false
      }),
      BooleanColumn({
        accessor: 'consumable',
        defaultVisible: false
      }),
      BooleanColumn({
        accessor: 'allow_variants',
        defaultVisible: false
      }),
      BooleanColumn({
        accessor: 'inherited',
        defaultVisible: false
      }),
      BooleanColumn({
        accessor: 'validated',
        defaultVisible: false
      }),
      {
        accessor: 'price_range',
        title: t`Unit Price`,
        ordering: 'pricing_max',
        sortable: true,
        switchable: true,
        defaultVisible: false,
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
        render: (record: any) => {
          const extra: ReactNode[] = [];

          const part = record.sub_part_detail;

          const available_stock: number = availableStockQuantity(record);
          const on_order: number = record?.on_order ?? 0;
          const building: number = record?.building ?? 0;

          if (part?.virtual) {
            return <Text fs='italic'>{t`Virtual part`}</Text>;
          }

          const text =
            available_stock <= 0 ? (
              <Text c='red' style={{ fontStyle: 'italic' }}>{t`No stock`}</Text>
            ) : (
              `${formatDecimal(available_stock)}`
            );

          if (record.external_stock > 0) {
            extra.push(
              <Text key='external'>
                {t`External stock`}: {formatDecimal(record.external_stock)}
              </Text>
            );
          }

          if (record.available_substitute_stock > 0) {
            extra.push(
              <Text key='substitute'>
                {t`Includes substitute stock`}:{' '}
                {formatDecimal(record.available_substitute_stock)}
              </Text>
            );
          }

          if (record.allow_variants && record.available_variant_stock > 0) {
            extra.push(
              <Text key='variant'>
                {t`Includes variant stock`}:{' '}
                {formatDecimal(record.available_variant_stock)}
              </Text>
            );
          }

          if (on_order > 0) {
            extra.push(
              <Text key='on_order'>
                {t`On order`}: {formatDecimal(on_order)}
              </Text>
            );
          }

          if (building > 0) {
            extra.push(
              <Text key='building'>
                {t`Building`}: {formatDecimal(building)}
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
          // Virtual sub-part - the "can build" quantity does not make sense here
          if (record.sub_part_detail?.virtual) {
            return '-';
          }

          // No information available
          if (record.can_build === null || record.can_build === undefined) {
            return '-';
          }

          // NaN or infinite values
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
              {formatDecimal(can_build)}
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
        name: 'sub_part_active',
        label: t`Active Part`,
        description: t`Show active items`
      },
      {
        name: 'sub_part_assembly',
        label: t`Assembled Part`,
        description: t`Show assembled items`
      },
      {
        name: 'sub_part_virtual',
        label: t`Virtual Part`,
        description: t`Show virtual items`
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
      },
      PartCategoryFilter()
    ];
  }, [partId, params]);

  const [selectedBomItem, setSelectedBomItem] = useState<any>({});

  const importSessionFields = useMemo(() => {
    const fields = dataImporterSessionFields({
      modelType: 'bomitem'
    });

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
    fields: bomItemFields({}),
    initialData: {
      part: partId
    },
    successMessage: t`BOM item created`,
    table: table
  });

  const editBomItem = useEditApiFormModal({
    url: ApiEndpoints.bom_list,
    pk: selectedBomItem.pk,
    title: t`Edit BOM Item`,
    fields: bomItemFields({}),
    successMessage: t`BOM item updated`,
    table: table
  });

  const deleteBomItem = useDeleteApiFormModal({
    url: ApiEndpoints.bom_list,
    pk: selectedBomItem.pk,
    title: t`Delete BOM Item`,
    successMessage: t`BOM item deleted`,
    table: table
  });

  const editSubstitues = useEditBomSubstitutesForm({
    bomItemId: selectedBomItem.pk,
    bomItem: selectedBomItem,
    onClose: () => {
      table.refreshTable();
    }
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
          onClick: () => {
            validateBomItem(record);
          }
        },
        RowEditAction({
          hidden: partLocked || !user.hasChangeRole(UserRoles.part),
          onClick: () => {
            setSelectedBomItem(record);
            editBomItem.open();
          }
        }),
        {
          title: t`Edit Substitutes`,
          color: 'blue',
          hidden: partLocked || !user.hasAddRole(UserRoles.part),
          icon: <IconSwitch3 />,
          onClick: () => {
            setSelectedBomItem(record);
            editSubstitues.open();
          }
        },
        RowDeleteAction({
          hidden: partLocked || !user.hasDeleteRole(UserRoles.part),
          onClick: () => {
            setSelectedBomItem(record);
            deleteBomItem.open();
          }
        })
      ];
    },
    [partId, partLocked, user]
  );

  const tableActions = useMemo(() => {
    return [
      <ActionDropdown
        key='add-bom-actions'
        tooltip={t`Add BOM Items`}
        position='bottom-start'
        icon={<IconPlus />}
        hidden={partLocked || !user.hasAddRole(UserRoles.part)}
        actions={[
          {
            name: t`Add BOM Item`,
            icon: <IconPlus />,
            tooltip: t`Add a single BOM item`,
            onClick: () => newBomItem.open()
          },
          {
            name: t`Import from File`,
            icon: <IconFileUpload />,
            tooltip: t`Import BOM items from a file`,
            onClick: () => importBomItem.open()
          }
        ]}
      />
    ];
  }, [partLocked, user]);

  return (
    <>
      {importBomItem.modal}
      {newBomItem.modal}
      {editBomItem.modal}
      {deleteBomItem.modal}
      {editSubstitues.modal}
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
              substitutes: true,
              part_detail: true,
              sub_part_detail: true,
              category_detail: true
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
