import { ActionButton } from '@lib/components/ActionButton';
import { StylishText } from '@lib/components/StylishText';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import { formatDecimal } from '@lib/functions/Formatting';
import { getDetailUrl } from '@lib/functions/Navigation';
import type {
  ApiFormAdjustFilterType,
  ApiFormFieldChoice,
  ApiFormFieldSet,
  ApiFormModalProps,
  StockOperationProps
} from '@lib/types/Forms';
import { t } from '@lingui/core/macro';
import {
  Alert,
  Collapse,
  Flex,
  Group,
  List,
  NumberInput,
  Paper,
  Skeleton,
  Stack,
  Table,
  Text,
  UnstyledButton
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { modals } from '@mantine/modals';
import {
  IconAlertTriangle,
  IconCalendarExclamation,
  IconChevronDown,
  IconChevronUp,
  IconCoin,
  IconCopy,
  IconLink,
  IconPackage,
  IconUsersGroup
} from '@tabler/icons-react';
import { useQuery, useSuspenseQuery } from '@tanstack/react-query';

import dayjs from 'dayjs';
import {
  type JSX,
  type ReactNode,
  Suspense,
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState
} from 'react';
import { useFormContext, useWatch } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { api } from '../App';
import RemoveRowButton from '../components/buttons/RemoveRowButton';
import {
  TableFieldExtraRow,
  TableFieldQuantityInput,
  type TableFieldRowProps
} from '../components/forms/fields/TableField';
import { Thumbnail } from '../components/images/Thumbnail';
import {
  StatusRenderer,
  getStatusCodeOptions
} from '../components/render/StatusRenderer';
import {
  RenderStockItem,
  RenderStockLocation
} from '../components/render/Stock';
import { StatusFilterOptions } from '../components/tables/Filter';
import { formatPriceRange } from '../defaults/formatters';
import { InvenTreeIcon } from '../functions/icons';
import {
  useApiFormModal,
  useBulkEditApiFormModal,
  useCreateApiFormModal,
  useDeleteApiFormModal
} from '../hooks/UseForm';
import {
  useBatchCodeGenerator,
  useSerialNumberGenerator
} from '../hooks/UseGenerator';
import useStatusCodes from '../hooks/UseStatusCodes';
import { useGlobalSettingsState } from '../states/SettingsStates';
import { useUserState } from '../states/UserState';
import { DuplicateField, TagsField } from './CommonFields';

/**
 * Construct a set of fields for creating / editing a StockItem instance
 */
export function useStockFields({
  partId,
  locationId,
  stockItem,
  create = false,
  supplierPartId,
  modalId,
  duplicateStockItem
}: {
  partId?: number;
  locationId?: number;
  stockItem?: any;
  modalId: string;
  create: boolean;
  supplierPartId?: number;
  duplicateStockItem?: any;
}): ApiFormFieldSet {
  const globalSettings = useGlobalSettingsState();
  const user = useUserState();

  // Keep track of the "part" instance
  const [partInstance, setPartInstance] = useState<any>({});

  const [supplierPart, setSupplierPart] = useState<number | null>(
    supplierPartId ?? null
  );

  // Keep track of the "location" for the new stock item
  const [location, setLocation] = useState<number | null>(locationId ?? null);

  const [expiryDate, setExpiryDate] = useState<string | null>(null);

  const batchGenerator = useBatchCodeGenerator({
    modalId: modalId,
    initialQuery: {
      part: partId
    }
  });

  const serialGenerator = useSerialNumberGenerator({
    modalId: modalId,
    initialQuery: {
      part: partId
    }
  });

  // Set the supplier part if provided
  useEffect(() => {
    if (supplierPartId && !supplierPart) setSupplierPart(supplierPartId);
  }, [partInstance, supplierPart, supplierPartId]);

  const stockItemStatusCodes = useStatusCodes({
    modelType: ModelType.stockitem
  });

  return useMemo(() => {
    const fields: ApiFormFieldSet = {
      part: {
        value: partInstance.pk,
        disabled: !create || !!partId,
        filters: {
          virtual: false,
          active: create ? true : undefined
        },
        onValueChange: (value, record) => {
          // Update the tracked part instance
          setPartInstance(record);

          serialGenerator.update({
            part: value
          });

          batchGenerator.update({
            part: value
          });

          // Clear the 'supplier_part' field if the part is changed
          setSupplierPart(null);

          // Adjust the 'expiry date' for the stock item
          const expiry_days = record?.default_expiry ?? 0;

          if (expiry_days && expiry_days > 0) {
            // Adjust the expiry date based on the part default expiry
            setExpiryDate(
              dayjs().add(expiry_days, 'days').format('YYYY-MM-DD')
            );
          }

          // Fill out the default location for the part, if not already set
          setLocation(
            (current) =>
              current ??
              record?.default_location ??
              record?.category_default_location ??
              null
          );
        }
      },
      supplier_part: {
        hidden: partInstance?.purchaseable == false,
        disabled: !!supplierPartId,
        value: supplierPart,
        onValueChange: (value) => {
          setSupplierPart(value);
        },
        filters: {
          part_detail: true,
          supplier_detail: true,
          part: partId
        },
        adjustFilters: (adjust: ApiFormAdjustFilterType) => {
          if (adjust.data.part) {
            adjust.filters['part'] = adjust.data.part;
          }

          return adjust.filters;
        }
      },
      use_pack_size: {
        hidden: !create,
        description: t`Add given quantity as packs instead of individual items`
      },
      location: {
        // Cannot adjust location for existing stock items
        hidden: !create,
        value: location,
        onValueChange: (value) => {
          setLocation(value);
          batchGenerator.update({ location: value });
        },
        filters: {
          structural: false
        }
      },
      quantity: {
        hidden: !create,
        description: t`Enter initial quantity for this stock item`,
        onValueChange: (value) => {
          batchGenerator.update({ quantity: value });
        }
      },
      serial_numbers: {
        field_type: 'string',
        label: t`Serial Numbers`,
        disabled: partInstance?.trackable == false,
        description: t`Enter serial numbers for new stock (or leave blank)`,
        required: false,
        hidden: !create,
        placeholderAutofill: true,
        placeholder: serialGenerator.result && `${serialGenerator.result}+`
      },
      serial: {
        placeholderAutofill: true,
        placeholder: serialGenerator.result,
        disabled: !create && !globalSettings.isSet('STOCK_ALLOW_EDIT_SERIAL'),
        hidden:
          create ||
          partInstance.trackable == false ||
          (stockItem?.quantity != undefined && stockItem?.quantity != 1)
      },
      batch: {
        default: '',
        placeholderAutofill: true,
        placeholder: batchGenerator.result
      },
      status_custom_key: {
        label: t`Stock Status`,
        default: stockItemStatusCodes.OK
      },
      expiry_date: {
        icon: <IconCalendarExclamation />,
        hidden: !globalSettings.isSet('STOCK_ENABLE_EXPIRY'),
        value: expiryDate,
        onValueChange: (value) => {
          setExpiryDate(value);
        }
      },
      packaging: {
        icon: <IconPackage />
      },
      tags: TagsField({}),
      link: {
        icon: <IconLink />
      },
      owner: {
        icon: <IconUsersGroup />
      },
      delete_on_deplete: {}
    };

    // Remove the expiry date field if it is not enabled
    if (!globalSettings.isSet('STOCK_ENABLE_EXPIRY')) {
      delete fields.expiry_date;
    }

    if (!create) {
      delete fields.serial_numbers;
    }

    // Additional fields for stock item duplication
    if (create && duplicateStockItem?.pk) {
      fields.duplicate = {
        icon: <IconCopy />,
        ...DuplicateField({
          originalId: duplicateStockItem.pk,
          extraFields: {
            copy_notes: { value: true },
            copy_tests: {
              value: false,
              hidden: !duplicateStockItem?.part_detail?.testable
            },
            // Costs are always copied by default - the option is only shown
            // to users who can view cost data
            copy_costs: {
              value: true,
              hidden: !user.hasViewRole(UserRoles.pricing)
            }
          }
        })
      };
    }

    return fields;
  }, [
    stockItem,
    expiryDate,
    partInstance,
    partId,
    globalSettings,
    supplierPart,
    location,
    create,
    supplierPartId,
    serialGenerator.result,
    batchGenerator.result,
    duplicateStockItem,
    create,
    user
  ]);
}

/**
 * Launch a form to create a new StockItem instance
 */
export function useCreateStockItem() {
  const fields = useStockFields({
    create: true,
    modalId: 'create-stock-item'
  });

  return useCreateApiFormModal({
    url: ApiEndpoints.stock_item_list,
    fields: fields,
    modalId: 'create-stock-item',
    title: t`Add Stock Item`,
    keepOpenOption: true
  });
}

/**
 * Form set for manually removing (uninstalling) a StockItem from an existing StockItem
 */
export function useStockItemUninstallFields(): ApiFormFieldSet {
  return useMemo(() => {
    return {
      location: {
        filters: {
          structural: false
        }
      },
      note: {}
    };
  }, []);
}

/**
 * Form set for manually installing a StockItem into an existing StockItem
 */
export function useStockItemInstallFields({
  stockItem
}: {
  stockItem: any;
}): ApiFormFieldSet {
  const globalSettings = useGlobalSettingsState();

  const [selectedPart, setSelectedPart] = useState<number | null>(null);

  useEffect(() => {
    setSelectedPart(null);
  }, [stockItem]);

  return useMemo(() => {
    // Note: The 'part' field is not a part of the API endpoint, so we construct it manually
    return {
      part: {
        field_type: 'related field',
        required: true,
        exclude: true,
        label: t`Part`,
        description: t`Select the part to install`,
        model: ModelType.part,
        api_url: apiUrl(ApiEndpoints.part_list),
        onValueChange: (value) => {
          setSelectedPart(value);
        },
        filters: {
          trackable: true,
          in_bom_for: globalSettings.isSet('STOCK_ENFORCE_BOM_INSTALLATION')
            ? stockItem.part
            : undefined
        }
      },
      stock_item: {
        disabled: !selectedPart,
        filters: {
          part_detail: true,
          in_stock: true,
          available: true,
          tracked: true,
          part: selectedPart ? selectedPart : undefined,
          include_variants: false
        }
      },
      quantity: {},
      note: {}
    };
  }, [globalSettings, selectedPart, stockItem]);
}

/**
 * Form set for serializing an existing StockItem
 */
export function useStockItemSerializeFields({
  partId,
  trackable,
  modalId
}: {
  partId: number;
  trackable: boolean;
  modalId: string;
}): ApiFormFieldSet {
  const serialGenerator = useSerialNumberGenerator({
    modalId: modalId,
    isEnabled: () => trackable,
    initialQuery: {
      part: partId
    }
  });

  return useMemo(() => {
    return {
      quantity: {},
      serial_numbers: {
        placeholder: serialGenerator.result && `${serialGenerator.result}+`,
        placeholderAutofill: true
      },
      destination: {}
    };
  }, [serialGenerator.result]);
}

/**
 * The outcome of the automatic cost allocation for a disassembly operation:
 *
 * - explicit: Every generated component has an explicit unit cost (nothing to allocate)
 * - allocate: The remaining cost of the assembly is allocated across the other components
 * - none: No cost is recorded for components without an explicit unit cost
 * - unknown: The user cannot view pricing data, so the outcome cannot be determined
 */
export type DisassemblyCostStatus = {
  mode: 'explicit' | 'allocate' | 'none' | 'unknown';
  reason?:
    | 'no-cost'
    | 'unconverted'
    | 'missing-pricing'
    | 'installed-unconverted'
    | 'no-remaining';
  // Components without pricing data (when reason = 'missing-pricing')
  missingParts: string[];
  // Installed items whose cost could not be converted (when reason = 'installed-unconverted')
  unconvertedItems?: string[];
  // Number of components without an explicit unit cost
  automaticCount: number;
  // Remaining cost to be allocated (if it can be calculated)
  remainingMin?: number;
  remainingMax?: number;
  currency?: string;
};

const DisassemblyCostContext = createContext<DisassemblyCostStatus | undefined>(
  undefined
);

function isBlankValue(value: any): boolean {
  return value === null || value === undefined || value === '';
}

/**
 * Return true if usable pricing data is available for the BOM line.
 * Mirrors StockItem.disassembly_cost_weights (server side)
 */
function bomLineHasPricing(record: any): boolean {
  const values = [record?.pricing_min, record?.pricing_max]
    .filter((value) => !isBlankValue(value))
    .map(Number);

  if (values.length == 0) {
    return false;
  }

  return values.reduce((a, b) => a + b, 0) / values.length > 0;
}

/**
 * Determine how component costs will be recorded for a disassembly operation.
 *
 * This mirrors StockItem.record_disassembly_costs (server side):
 * - Components with an explicit unit cost are recorded at that cost
 * - The remaining cost of the assembly (less installed items and explicit costs)
 *   is allocated across the other components, weighted by part pricing -
 *   but *only* if pricing data is available for every one of those components
 * - Otherwise, no cost is recorded for components without an explicit unit cost
 */
export function getDisassemblyCostStatus({
  stockItem,
  lines,
  records,
  installedMap,
  installedItems,
  quantity,
  canViewPricing,
  defaultCurrency
}: {
  stockItem: any;
  lines: any[];
  records: Record<number, any>;
  installedMap: Record<number, any[]>;
  installedItems: any[];
  quantity: any;
  canViewPricing: boolean;
  defaultCurrency: string;
}): DisassemblyCostStatus {
  // Quantity of new stock items created for each line (installed items are broken out instead)
  const created = lines
    .map((line: any) => {
      const installed = (installedMap[line.bom_item] ?? []).reduce(
        (total: number, item: any) => total + (Number(item.quantity) || 0),
        0
      );

      return {
        line: line,
        record: records[line.bom_item],
        quantity: Math.max(0, (Number(line.quantity) || 0) - installed)
      };
    })
    .filter((entry) => entry.quantity > 0);

  const explicit = created.filter(
    (entry) => !isBlankValue(entry.line.unit_cost)
  );
  const automatic = created.filter((entry) =>
    isBlankValue(entry.line.unit_cost)
  );

  const status: DisassemblyCostStatus = {
    mode: 'explicit',
    missingParts: [],
    automaticCount: automatic.length
  };

  if (automatic.length == 0) {
    return status;
  }

  if (!canViewPricing) {
    return { ...status, mode: 'unknown' };
  }

  const cost = stockItem?.pricing_detail;
  const minCost = cost?.min_cost ?? cost?.max_cost;
  const maxCost = cost?.max_cost ?? cost?.min_cost;

  if (isBlankValue(minCost) || isBlankValue(maxCost)) {
    // A cost summary without values means the cost could not be converted
    return {
      ...status,
      mode: 'none',
      reason: cost?.incomplete ? 'unconverted' : 'no-cost'
    };
  }

  const missing = automatic
    .filter((entry) => !bomLineHasPricing(entry.record))
    .map((entry) => entry.record?.sub_part_detail?.full_name ?? '-');

  if (missing.length > 0) {
    return {
      ...status,
      mode: 'none',
      reason: 'missing-pricing',
      missingParts: missing
    };
  }

  // An installed item with a cost summary but no values (its cost could not be converted)
  // means the remaining cost cannot be determined - so no cost is allocated.
  // Mirrors StockItem.disassembly_cost_pool (server side)
  const unconverted = installedItems.filter(
    (item: any) =>
      !!item.pricing_detail &&
      isBlankValue(item.pricing_detail.min_cost) &&
      isBlankValue(item.pricing_detail.max_cost)
  );

  if (unconverted.length > 0) {
    return {
      ...status,
      mode: 'none',
      reason: 'installed-unconverted',
      unconvertedItems: unconverted.map((item: any) => {
        const name = item.part_detail?.full_name ?? '-';
        return item.serial ? `${name} #${item.serial}` : name;
      })
    };
  }

  // The remaining cost can only be calculated if all values are in the same currency
  // (explicit costs are entered in the default currency)
  const sameCurrency =
    cost.currency == defaultCurrency &&
    installedItems.every(
      (item: any) =>
        !item.pricing_detail || item.pricing_detail.currency == defaultCurrency
    );

  if (!sameCurrency) {
    return { ...status, mode: 'allocate' };
  }

  const n = Number(quantity) || 0;

  let installedMin = 0;
  let installedMax = 0;

  for (const item of installedItems) {
    const itemCost = item.pricing_detail;

    if (!itemCost) {
      continue;
    }

    const values = [itemCost.min_cost, itemCost.max_cost]
      .filter((value) => !isBlankValue(value))
      .map(Number);

    if (values.length > 0) {
      installedMin += Math.min(...values) * (Number(item.quantity) || 0);
      installedMax += Math.max(...values) * (Number(item.quantity) || 0);
    }
  }

  const explicitTotal = explicit.reduce(
    (total: number, entry) =>
      total + (Number(entry.line.unit_cost) || 0) * entry.quantity,
    0
  );

  // Interval subtraction (mirrors StockItem.disassembly_cost_pool):
  // the minimum remaining cost deducts the *maximum* installed cost, and vice versa
  const remainingMin = Math.max(
    0,
    Number(minCost) * n - installedMax - explicitTotal
  );
  const remainingMax = Math.max(
    0,
    Number(maxCost) * n - installedMin - explicitTotal
  );

  if (remainingMax <= 0) {
    return { ...status, mode: 'none', reason: 'no-remaining' };
  }

  return {
    ...status,
    mode: 'allocate',
    remainingMin: remainingMin,
    remainingMax: remainingMax,
    currency: defaultCurrency
  };
}

/**
 * Explain how component costs will be recorded for a disassembly operation
 */
function DisassemblyCostInfo({
  status
}: Readonly<{
  status: DisassemblyCostStatus;
}>) {
  switch (status.mode) {
    case 'allocate': {
      const count = status.automaticCount;
      const amount =
        status.remainingMax === undefined
          ? ''
          : String(
              formatPriceRange(
                status.remainingMin ?? null,
                status.remainingMax ?? null,
                { currency: status.currency }
              )
            );

      return (
        <Alert
          color='blue'
          icon={<IconCoin />}
          title={t`Automatic Cost Allocation`}
        >
          <Text size='sm'>
            {amount
              ? t`The remaining cost of this stock item (${amount}) will be allocated across the ${count} component(s) without a unit cost, weighted by part pricing.`
              : t`The remaining cost of this stock item will be allocated across the ${count} component(s) without a unit cost, weighted by part pricing.`}
          </Text>
          <Text size='xs' c='dimmed'>
            {t`The remaining cost excludes any unit costs entered above, and the cost of any installed items (which keep their own costs).`}
          </Text>
        </Alert>
      );
    }
    case 'none': {
      const count = status.automaticCount;
      let reason: ReactNode = null;

      switch (status.reason) {
        case 'no-cost':
          reason = t`This stock item does not have a recorded cost.`;
          break;
        case 'unconverted':
          reason = t`The cost of this stock item could not be converted to the default currency (no exchange rate is available).`;
          break;
        case 'missing-pricing':
          reason = (
            <Stack gap={2}>
              <Text size='sm'>
                {t`Part pricing data is not available for the following components:`}
              </Text>
              <List size='sm'>
                {status.missingParts.map((name: string, idx: number) => (
                  <List.Item key={`${name}-${idx}`}>{name}</List.Item>
                ))}
              </List>
            </Stack>
          );
          break;
        case 'installed-unconverted':
          reason = (
            <Stack gap={2}>
              <Text size='sm'>
                {t`The cost of the following installed items could not be converted to the default currency (no exchange rate is available), so the remaining cost cannot be determined:`}
              </Text>
              <List size='sm'>
                {(status.unconvertedItems ?? []).map(
                  (name: string, idx: number) => (
                    <List.Item key={`${name}-${idx}`}>{name}</List.Item>
                  )
                )}
              </List>
            </Stack>
          );
          break;
        case 'no-remaining':
          reason = t`The cost of this stock item is already accounted for by the unit costs entered above and the cost of any installed items.`;
          break;
      }

      return (
        <Alert
          color='orange'
          icon={<IconAlertTriangle />}
          title={t`No Cost Will Be Recorded`}
        >
          <Stack gap='xs'>
            <Text size='sm' fw={500}>
              {t`No cost will be recorded for the ${count} component(s) without a unit cost.`}
            </Text>
            {typeof reason === 'string' ? (
              <Text size='sm'>{reason}</Text>
            ) : (
              reason
            )}
            <Text size='sm'>
              {t`To record a cost for these components, enter a unit cost for each of them.`}
            </Text>
          </Stack>
        </Alert>
      );
    }
    case 'unknown':
      return (
        <Alert color='blue' icon={<IconCoin />} title={t`Component Costs`}>
          <Text size='sm'>
            {t`Components with a unit cost are recorded at that cost. The remaining cost of this stock item is only allocated to the other components if this stock item has a recorded cost and part pricing data is available for every one of them. Otherwise, no cost is recorded for components without a unit cost.`}
          </Text>
        </Alert>
      );
    default:
      return null;
  }
}

function DisassemblyLineRow({
  props,
  record,
  installedItems,
  serialized,
  statuses
}: Readonly<{
  props: TableFieldRowProps;
  record: any;
  installedItems: any[];
  serialized: boolean;
  statuses: any;
}>) {
  // Number of assemblies being disassembled (top-level form field)
  const assemblies = useWatch({ name: 'quantity' });

  // Once the user manually edits the row quantity, stop auto-scaling it
  const [edited, setEdited] = useState<boolean>(false);

  const [installedOpen, installedHandlers] = useDisclosure(false);

  // How costs are recorded for lines without an explicit unit cost
  const costStatus = useContext(DisassemblyCostContext);

  const [locationOpen, locationHandlers] = useDisclosure(false, {
    onClose: () => props.changeFn(props.rowId, 'location', undefined)
  });

  const [statusOpen, statusHandlers] = useDisclosure(false, {
    onClose: () => props.changeFn(props.rowId, 'status', undefined)
  });

  useEffect(() => {
    if (edited) {
      return;
    }

    const n = Number(assemblies);
    const unit = Number(record.quantity);

    if (Number.isFinite(n) && Number.isFinite(unit)) {
      const expected = unit * n;

      if (props.item.quantity !== expected) {
        props.changeFn(props.rowId, 'quantity', expected);
      }
    }
  }, [assemblies, edited]);

  return (
    <>
      <Table.Tr>
        <Table.Td>
          <Group gap='xs' justify='left' wrap='nowrap'>
            <Thumbnail
              size={32}
              src={record.sub_part_detail?.thumbnail}
              align='center'
            />
            <Stack gap={2}>
              <div>{record.sub_part_detail?.name}</div>
              {installedItems.length > 0 && (
                <UnstyledButton
                  onClick={() => installedHandlers.toggle()}
                  aria-label={`toggle-installed-items-${props.rowId}`}
                >
                  <Group gap={4} wrap='nowrap'>
                    {installedOpen ? (
                      <IconChevronUp size={14} />
                    ) : (
                      <IconChevronDown size={14} />
                    )}
                    <Text size='xs' c='blue'>
                      {t`Installed Items`}: {installedItems.length}
                    </Text>
                  </Group>
                </UnstyledButton>
              )}
            </Stack>
          </Group>
        </Table.Td>
        <Table.Td>{record.quantity}</Table.Td>
        <Table.Td style={{ whiteSpace: 'nowrap' }}>
          {serialized ? (
            // Quantity is fixed when disassembling a serialized stock item
            <Text size='sm' aria-label='text-field-quantity'>
              {formatDecimal(props.item.quantity)}
            </Text>
          ) : (
            <TableFieldQuantityInput
              min={0}
              value={props.item.quantity ?? ''}
              onChange={(value) => {
                setEdited(true);
                props.changeFn(props.rowId, 'quantity', value);
              }}
              error={props.rowErrors?.quantity?.message}
            />
          )}
        </Table.Td>
        <Table.Td style={{ whiteSpace: 'nowrap' }}>
          <NumberInput
            radius='sm'
            aria-label='number-field-unit_cost'
            placeholder={
              costStatus?.mode == 'none' ? t`No cost recorded` : t`Automatic`
            }
            min={0}
            decimalScale={6}
            value={props.item.unit_cost ?? ''}
            onChange={(value) => {
              props.changeFn(
                props.rowId,
                'unit_cost',
                value === '' ? null : value
              );
            }}
            error={props.rowErrors?.unit_cost?.message}
          />
        </Table.Td>
        <Table.Td style={{ width: '1%', whiteSpace: 'nowrap' }}>
          <Flex gap='1px'>
            <ActionButton
              size='sm'
              onClick={() => locationHandlers.toggle()}
              icon={<InvenTreeIcon icon='location' />}
              tooltip={t`Set Location`}
              tooltipAlignment='top'
              variant={locationOpen ? 'outline' : 'transparent'}
            />
            <ActionButton
              size='sm'
              onClick={() => statusHandlers.toggle()}
              icon={<InvenTreeIcon icon='status' />}
              tooltip={t`Change Status`}
              tooltipAlignment='top'
              variant={statusOpen ? 'outline' : 'transparent'}
            />
          </Flex>
        </Table.Td>
        <Table.Td>
          <RemoveRowButton
            onClick={() => props.removeFn(props.rowId)}
            disabled={installedItems.length > 0}
            tooltip={
              installedItems.length > 0
                ? t`This row cannot be removed as it has installed items`
                : undefined
            }
          />
        </Table.Td>
      </Table.Tr>
      {installedItems.length > 0 && (
        <Table.Tr>
          <Table.Td colSpan={6} style={{ padding: 0, borderBottom: 'none' }}>
            <Collapse expanded={installedOpen}>
              <Paper p='xs' pl='xl'>
                <Stack gap='xs'>
                  <Text size='xs' c='dimmed'>
                    {t`The following installed items will be uninstalled during disassembly`}
                  </Text>
                  {installedItems.map((item: any) => (
                    <RenderStockItem key={item.pk} instance={item} />
                  ))}
                </Stack>
              </Paper>
            </Collapse>
          </Table.Td>
        </Table.Tr>
      )}
      <TableFieldExtraRow
        visible={locationOpen}
        fieldName='location'
        onValueChange={(value) =>
          props.changeFn(props.rowId, 'location', value)
        }
        fieldDefinition={{
          field_type: 'related field',
          model: ModelType.stocklocation,
          api_url: apiUrl(ApiEndpoints.stock_location_list),
          filters: {
            structural: false
          },
          value: props.item.location,
          label: t`Location`,
          description: t`Custom location for the component items`,
          icon: <InvenTreeIcon icon='location' />
        }}
        error={props.rowErrors?.location?.message}
      />
      <TableFieldExtraRow
        visible={statusOpen}
        fieldName='status'
        defaultValue={10}
        onValueChange={(value) => props.changeFn(props.rowId, 'status', value)}
        fieldDefinition={{
          field_type: 'choice',
          api_url: apiUrl(ApiEndpoints.stock_status),
          choices: statuses,
          label: t`Status`,
          description: t`Status for the component items`
        }}
        error={props.rowErrors?.status?.message}
      />
    </>
  );
}

/**
 * Display a summary of the stock item which is about to be disassembled.
 */
function DisassemblyItemInfo({
  stockItem
}: Readonly<{
  stockItem: any;
}>) {
  const serialized: boolean =
    !!stockItem.serial && Number(stockItem.quantity) == 1;

  const details: { label: string; value: ReactNode }[] = useMemo(() => {
    const rows = [
      {
        label: t`Location`,
        value: stockItem.location_detail?.pathstring ?? t`No location set`
      }
    ];

    if (serialized) {
      rows.push({
        label: t`Serial Number`,
        value: stockItem.serial
      });
    } else {
      rows.push({
        label: t`Quantity`,
        value: formatDecimal(stockItem.quantity)
      });
    }

    if (stockItem.batch) {
      rows.push({
        label: t`Batch Code`,
        value: stockItem.batch
      });
    }

    return rows;
  }, [stockItem, serialized]);

  return (
    <Paper withBorder p='sm'>
      <Group gap='md' wrap='nowrap' align='center'>
        <Thumbnail
          size={56}
          src={stockItem.part_detail?.thumbnail}
          align='center'
        />
        <Group grow wrap='nowrap'>
          <Stack gap={2}>
            <Text fw={700}>
              {stockItem.part_detail?.full_name ?? stockItem.part_detail?.name}
            </Text>
            {stockItem.part_detail?.description && (
              <Text size='sm' c='dimmed'>
                {stockItem.part_detail.description}
              </Text>
            )}
          </Stack>
          <Table withRowBorders={false} verticalSpacing={2}>
            <Table.Tbody>
              {details.map((row) => (
                <Table.Tr key={row.label}>
                  <Table.Td style={{ width: '1%', whiteSpace: 'nowrap' }}>
                    <Text size='sm' c='dimmed'>
                      {row.label}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Text size='sm'>{row.value}</Text>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        </Group>
      </Group>
    </Paper>
  );
}

/**
 * Display any installed stock items which could not be matched
 * against a BOM line item for the disassembly operation.
 */
function DisassemblyLeftoverItems({
  items
}: Readonly<{
  items: any[];
}>) {
  if (items.length == 0) {
    return null;
  }

  return (
    <Alert
      color='yellow'
      icon={<IconPackage />}
      title={t`Additional Installed Items`}
    >
      <Stack gap='xs'>
        <Text size='sm'>
          {t`The following items are installed within this stock item, but do not match a listed component. They will be uninstalled during disassembly.`}
        </Text>
        {items.map((item: any) => (
          <RenderStockItem key={item.pk} instance={item} />
        ))}
      </Stack>
    </Alert>
  );
}

/**
 * Form for disassembling a stock item into its component parts,
 * based on the Bill of Materials for the associated part.
 */
export function useDisassembleStockItem({
  stockItem,
  refresh
}: {
  stockItem: any;
  refresh: () => void;
}) {
  // Fetch BOM lines for the part associated with the stock item
  const bomQuery = useQuery({
    queryKey: ['bom-items-disassemble', stockItem.pk, stockItem.part],
    enabled: !!stockItem.part && (stockItem.part_detail?.assembly ?? false),
    queryFn: async () =>
      api
        .get(apiUrl(ApiEndpoints.bom_list), {
          params: {
            part: stockItem.part,
            sub_part_detail: true,
            substitutes: true,
            // Part pricing data (only returned for users with the 'pricing' view role)
            // is used to explain how component costs will be recorded
            pricing: true
          }
        })
        .then((response) => response.data ?? [])
  });

  // Fetch any stock items which are installed within this stock item
  const installedQuery = useQuery({
    queryKey: ['installed-items-disassemble', stockItem.pk],
    enabled: !!stockItem.pk && (stockItem.part_detail?.assembly ?? false),
    queryFn: async () =>
      api
        .get(apiUrl(ApiEndpoints.stock_item_list), {
          params: {
            belongs_to: stockItem.pk,
            part_detail: true,
            // Cost data (only returned for users with the 'pricing' view role)
            pricing_detail: true
          }
        })
        .then((response) => response.data ?? [])
  });

  const bomItems: any[] = useMemo(() => {
    // Consumable BOM lines are excluded from disassembly,
    // as are any lines which point to a virtual part
    return (bomQuery.data ?? []).filter(
      (elem: any) =>
        !elem.consumable &&
        !elem.sub_part_detail?.consumable &&
        !elem.sub_part_detail?.virtual
    );
  }, [bomQuery.data]);

  const records = useMemo(
    () => Object.fromEntries(bomItems.map((elem: any) => [elem.pk, elem])),
    [bomItems]
  );

  // Map installed stock items against the available BOM lines.
  // Note: This mirrors the matching performed by the server during disassembly,
  // matching against the referenced sub_part or any designated substitute parts.
  // Variants of the sub_part cannot be resolved client-side, so any such items
  // are reported as "leftover" items instead.
  const { installedMap, leftoverItems } = useMemo(() => {
    const map: Record<number, any[]> = {};
    const leftover: any[] = [];

    for (const item of installedQuery.data ?? []) {
      const bomItem = bomItems.find(
        (elem: any) =>
          elem.sub_part === item.part ||
          elem.substitutes?.some((sub: any) => sub.part === item.part)
      );

      if (bomItem) {
        map[bomItem.pk] = [...(map[bomItem.pk] ?? []), item];
      } else {
        leftover.push(item);
      }
    }

    return { installedMap: map, leftoverItems: leftover };
  }, [bomItems, installedQuery.data]);

  // A serialized stock item must be disassembled in its entirety
  const serialized: boolean =
    !!stockItem.serial && Number(stockItem.quantity) == 1;

  // Explicit (per line) unit costs are entered in the default currency
  const globalSettings = useGlobalSettingsState();

  const defaultCurrency: string =
    globalSettings.getSetting('INVENTREE_DEFAULT_CURRENCY') || 'USD';

  const stockStatusCodes = useMemo(
    () => getStatusCodeOptions(ModelType.stockitem),
    []
  );

  const user = useUserState();

  const canViewPricing: boolean = useMemo(
    () => user.hasViewRole(UserRoles.pricing),
    [user]
  );

  const initialLines: any[] = useMemo(
    () =>
      bomItems.map((elem: any) => {
        return {
          id: elem.pk,
          bom_item: elem.pk,
          quantity:
            (Number(elem.quantity) || 0) * (Number(stockItem.quantity) || 0),
          // Explicit unit cost (in the default currency) - leave blank for automatic allocation
          unit_cost: null
        };
      }),
    [bomItems, stockItem.quantity]
  );

  // Track the current form values, to explain how component costs will be recorded
  const [formLines, setFormLines] = useState<any[]>([]);
  const [formQuantity, setFormQuantity] = useState<any>(stockItem.quantity);

  const resetCostState = useCallback(() => {
    setFormLines(initialLines);
    setFormQuantity(stockItem.quantity);
  }, [initialLines, stockItem.quantity]);

  useEffect(() => {
    resetCostState();
  }, [resetCostState]);

  const costStatus: DisassemblyCostStatus = useMemo(
    () =>
      getDisassemblyCostStatus({
        stockItem: stockItem,
        lines: formLines,
        records: records,
        installedMap: installedMap,
        installedItems: installedQuery.data ?? [],
        quantity: formQuantity,
        canViewPricing: canViewPricing,
        defaultCurrency: defaultCurrency
      }),
    [
      stockItem,
      formLines,
      records,
      installedMap,
      installedQuery.data,
      formQuantity,
      canViewPricing,
      defaultCurrency
    ]
  );

  const fields: ApiFormFieldSet = useMemo(() => {
    return {
      quantity: {
        disabled: serialized,
        onValueChange: (value: any) => setFormQuantity(value)
      },
      location: {
        filters: {
          structural: false
        }
      },
      items: {
        field_type: 'table',
        value: initialLines,
        onValueChange: (value: any) => setFormLines(value ?? []),
        modelRenderer: (row: TableFieldRowProps) => {
          const record = records[row.item.bom_item];

          if (!record) {
            return null;
          }

          return (
            <DisassemblyLineRow
              props={row}
              record={record}
              installedItems={installedMap[row.item.bom_item] ?? []}
              serialized={serialized}
              statuses={stockStatusCodes}
              key={row.rowId}
            />
          );
        },
        headers: [
          { title: t`Component`, style: { minWidth: '200px' } },
          { title: t`Unit Quantity`, style: { width: '100px' } },
          { title: t`Quantity`, style: { width: '200px' } },
          {
            title: `${t`Unit Cost`} (${defaultCurrency})`,
            style: { width: '200px' }
          },
          { title: t`Actions` },
          { title: '', style: { width: '50px' } }
        ]
      },
      notes: {}
    };
  }, [
    initialLines,
    records,
    installedMap,
    serialized,
    stockStatusCodes,
    defaultCurrency
  ]);

  const form = useCreateApiFormModal({
    url: ApiEndpoints.stock_disassemble,
    pk: stockItem.pk,
    title: t`Disassemble Stock Item`,
    fields: fields,
    preFormContent: <DisassemblyItemInfo stockItem={stockItem} />,
    postFormContent: (
      <Stack gap='xs'>
        <DisassemblyCostInfo status={costStatus} />
        <DisassemblyLeftoverItems items={leftoverItems} />
      </Stack>
    ),
    initialData: {
      quantity: stockItem.quantity,
      location: stockItem.location
    },
    size: '80%',
    successMessage: t`Stock item disassembled`,
    onFormSuccess: refresh,
    onOpen: () => {
      // Ensure the installed items data is up to date when the form is opened
      installedQuery.refetch();
      resetCostState();
    }
  });

  // Provide the cost status to each line (rendered within the form)
  return {
    ...form,
    modal: (
      <DisassemblyCostContext.Provider value={costStatus}>
        {form.modal}
      </DisassemblyCostContext.Provider>
    )
  };
}

function StockItemDefaultMove({
  stockItem,
  value
}: Readonly<{
  stockItem: any;
  value: any;
}>) {
  const { data } = useSuspenseQuery({
    queryKey: [
      'location',
      stockItem.part_detail?.default_location ??
        stockItem.part_detail?.category_default_location
    ],
    queryFn: async () => {
      const url = apiUrl(
        ApiEndpoints.stock_location_list,
        stockItem.part_detail?.default_location ??
          stockItem.part_detail?.category_default_location
      );

      return api
        .get(url)
        .then((response) => {
          switch (response.status) {
            case 200:
              return response.data;
            default:
              return null;
          }
        })
        .catch(() => {
          return null;
        });
    }
  });

  return (
    <Flex gap='sm' justify='space-evenly' align='center'>
      <Flex gap='sm' direction='column' align='center'>
        <Text>
          {value} x {stockItem.part_detail.name}
        </Text>
        <Thumbnail
          src={stockItem.part_detail.thumbnail}
          size={80}
          align='center'
        />
      </Flex>
      <Flex direction='column' gap='sm' align='center'>
        <Text>{stockItem.location_detail?.pathstring ?? '-'}</Text>
        <InvenTreeIcon icon='arrow_down' />
        <Suspense fallback={<Skeleton width='150px' />}>
          <Text>{data?.pathstring}</Text>
        </Suspense>
      </Flex>
    </Flex>
  );
}

function moveToDefault(
  stockItem: any,
  value: StockItemQuantity,
  refresh: () => void,
  options?: {
    title?: string;
    onConfirm?: (location: number) => void;
  }
) {
  const location =
    stockItem.part_detail?.default_location ??
    stockItem.part_detail?.category_default_location;

  modals.openConfirmModal({
    title: (
      <StylishText>{options?.title ?? t`Confirm Stock Transfer`}</StylishText>
    ),
    children: <StockItemDefaultMove stockItem={stockItem} value={value} />,
    onConfirm: () => {
      if (!location) {
        return;
      }

      if (options?.onConfirm) {
        options.onConfirm(location);
        return;
      }

      if (
        stockItem.location === stockItem.part_detail?.default_location ||
        stockItem.location === stockItem.part_detail?.category_default_location
      ) {
        return;
      }
      api
        .post(apiUrl(ApiEndpoints.stock_transfer), {
          items: [
            {
              pk: stockItem.pk,
              quantity: value,
              batch: stockItem.batch,
              status: stockItem.status
            }
          ],
          location: location
        })
        .then((response) => {
          refresh();
          return response.data;
        })
        .catch(() => {
          return null;
        });
    }
  });
}

/*
 * Memoize a list of stock items for use in a stock operations modal.
 * These items may be provided directly, or fetched from the API
 *
 * @param opened - Is the underlying modal opened or closed?
 * @param items - Optional list of stock items to use directly
 * @param category - Optional category ID to filter stock items
 * @param location - Optional location ID to filter stock items
 * @param part - Optional part ID to filter stock items
 * @param filters - Optional additional filters to apply to the stock item query
 */
function useStockItems({
  opened,
  items,
  filters
}: Readonly<{
  opened: boolean;
  items?: any[] | any;
  filters?: { [key: string]: any };
}>) {
  // Only query the API if the items are not provided directly
  const query = useQuery({
    enabled: opened && items === undefined,
    queryKey: ['stockItems', filters],
    queryFn: async () => {
      if (!opened) {
        return [];
      }

      // Fetch via the API
      const url = apiUrl(ApiEndpoints.stock_item_list);

      return api
        .get(url, {
          params: {
            ...filters,
            part_detail: true,
            location_detail: true,
            cascade: false
          }
        })
        .then((response) => response.data ?? []);
    }
  });

  return useMemo(() => {
    if (!opened) {
      return [];
    }

    if (items !== undefined) {
      return Array.isArray(items) ? items : [items];
    }

    return query.data ?? [];
  }, [opened, items, query.data]);
}

function ReturnStockMoveButton({
  record,
  quantity,
  onRemove,
  returnStock
}: {
  record: any;
  quantity: StockItemQuantity;
  onRemove: () => void;
  returnStock: boolean;
}) {
  const form = useFormContext();

  return (
    <ActionButton
      onClick={() =>
        moveToDefault(
          record,
          quantity,
          onRemove,
          returnStock
            ? {
                title: t`Confirm Stock Return`,
                onConfirm: (location: number) => {
                  form.setValue('location', location, {
                    shouldDirty: true,
                    shouldValidate: true
                  });
                }
              }
            : undefined
        )
      }
      icon={<InvenTreeIcon icon='default_location' />}
      tooltip={t`Move to default location`}
      tooltipAlignment='top'
      disabled={
        !record.part_detail?.default_location &&
        !record.part_detail?.category_default_location
      }
    />
  );
}

function StockOperationsRow({
  props,
  transfer = false,
  changeStatus = false,
  add = false,
  setMax = false,
  merge = false,
  transferMerge = false,
  returnStock = false,
  record
}: {
  props: TableFieldRowProps;
  transfer?: boolean;
  changeStatus?: boolean;
  add?: boolean;
  setMax?: boolean;
  merge?: boolean;
  transferMerge?: boolean;
  returnStock?: boolean;
  record?: any;
}) {
  const rowId = props.rowId;

  const statusOptions: ApiFormFieldChoice[] = useMemo(() => {
    return (
      StatusFilterOptions(ModelType.stockitem)()?.map((choice) => {
        return {
          value: choice.value,
          display_name: choice.label
        };
      }) ?? []
    );
  }, []);

  const [quantity, setQuantity] = useState<StockItemQuantity>(
    add ? 0 : (props.item?.quantity ?? 0)
  );

  const [status, setStatus] = useState<number | undefined>(undefined);

  const [packagingOpen, packagingHandlers] = useDisclosure(false);
  const [statusOpen, statusHandlers] = useDisclosure(false);
  const hasMountedPackagingRef = useRef(false);
  const hasMountedStatusRef = useRef(false);

  useEffect(() => {
    if (!transfer) {
      return;
    }

    if (!hasMountedPackagingRef.current) {
      hasMountedPackagingRef.current = true;
      return;
    }

    props.changeFn(
      rowId,
      'packaging',
      packagingOpen ? record?.packaging || undefined : undefined
    );
  }, [transfer, packagingOpen, rowId, record?.packaging, props.changeFn]);

  useEffect(() => {
    if (!changeStatus) {
      return;
    }

    if (!hasMountedStatusRef.current) {
      hasMountedStatusRef.current = true;
      return;
    }

    if (statusOpen) {
      setStatus(record?.status_custom_key || record?.status || undefined);
      props.changeFn(rowId, 'status', record?.status || undefined);
      return;
    }

    setStatus(undefined);
    props.changeFn(rowId, 'status', undefined);
  }, [
    changeStatus,
    statusOpen,
    rowId,
    record?.status,
    record?.status_custom_key,
    props.changeFn
  ]);

  const stockString: string = useMemo(() => {
    if (!record) {
      return '-';
    }

    if (!record.serial) {
      return `${record.quantity}`;
    } else {
      return `#${record.serial}`;
    }
  }, [record]);

  return !record ? (
    <Table.Tr>
      <Table.Td colSpan={6}>{t`Loading...`}</Table.Td>
    </Table.Tr>
  ) : (
    <>
      <Table.Tr
        aria-label={`stock-op-row-${rowId}`}
        key={`stock-op-row-${rowId}`}
      >
        <Table.Td>
          <Stack gap='xs'>
            <Flex gap='sm' align='center'>
              <Thumbnail
                size={40}
                src={record.part_detail?.thumbnail}
                align='center'
              />
              <div>{record.part_detail?.name}</div>
            </Flex>
            {props.rowErrors?.pk?.message && (
              <Text c='red' size='xs'>
                {props.rowErrors.pk.message}
              </Text>
            )}
          </Stack>
        </Table.Td>
        <Table.Td>
          <RenderStockLocation instance={record.location_detail} />
        </Table.Td>
        <Table.Td>{record.batch ? record.batch : '-'}</Table.Td>
        <Table.Td>
          <Group grow justify='space-between' wrap='nowrap'>
            <Text>{stockString}</Text>
            <StatusRenderer
              status={record.status_custom_key || record.status}
              fallbackStatus={record.status}
              type={ModelType.stockitem}
            />
          </Group>
        </Table.Td>
        {!merge && (
          <Table.Td>
            <TableFieldQuantityInput
              min={0}
              value={quantity ?? ''}
              onChange={(value) => {
                setQuantity(value);
                props.changeFn(rowId, 'quantity', value);
              }}
              error={props.rowErrors?.quantity?.message}
            />
          </Table.Td>
        )}
        <Table.Td>
          <Flex gap='3px'>
            {transfer &&
              (returnStock ? (
                <ReturnStockMoveButton
                  record={record}
                  quantity={props.item.quantity}
                  onRemove={() => props.removeFn(rowId)}
                  returnStock={returnStock}
                />
              ) : (
                <ActionButton
                  onClick={() =>
                    moveToDefault(record, props.item.quantity, () =>
                      props.removeFn(rowId)
                    )
                  }
                  icon={<InvenTreeIcon icon='default_location' />}
                  tooltip={t`Move to default location`}
                  tooltipAlignment='top'
                  disabled={
                    !record.part_detail?.default_location &&
                    !record.part_detail?.category_default_location
                  }
                />
              ))}
            {changeStatus && (
              <ActionButton
                size='sm'
                icon={<InvenTreeIcon icon='status' />}
                tooltip={t`Change Status`}
                onClick={() => statusHandlers.toggle()}
                variant={statusOpen ? 'filled' : 'transparent'}
              />
            )}
            {transfer && (
              <ActionButton
                size='sm'
                icon={<InvenTreeIcon icon='packaging' />}
                tooltip={t`Adjust Packaging`}
                onClick={() => packagingHandlers.toggle()}
                variant={packagingOpen ? 'filled' : 'transparent'}
              />
            )}
            {transferMerge && (
              <ActionButton
                size='sm'
                icon={<InvenTreeIcon icon='merge' />}
                tooltip={t`Merge into existing stock`}
                onClick={() =>
                  props.changeFn(rowId, 'merge', !props.item?.merge)
                }
                variant={props.item?.merge ? 'filled' : 'transparent'}
              />
            )}
            <RemoveRowButton onClick={() => props.removeFn(rowId)} />
          </Flex>
        </Table.Td>
      </Table.Tr>
      {changeStatus && (
        <TableFieldExtraRow
          visible={statusOpen}
          onValueChange={(value: any) => {
            setStatus(value);
            props.changeFn(rowId, 'status', value || undefined);
          }}
          fieldName='status'
          fieldDefinition={{
            field_type: 'choice',
            label: t`Status`,
            choices: statusOptions,
            value: status
          }}
          defaultValue={status}
        />
      )}
      {transfer && (
        <TableFieldExtraRow
          visible={transfer && packagingOpen}
          onValueChange={(value: any) => {
            props.changeFn(rowId, 'packaging', value || undefined);
          }}
          fieldName='packaging'
          fieldDefinition={{
            field_type: 'string',
            label: t`Packaging`
          }}
          defaultValue={record.packaging}
        />
      )}
    </>
  );
}

type StockItemQuantity = number | '' | undefined;

type StockAdjustmentItem = {
  pk: number;
  quantity: StockItemQuantity;
  batch?: string;
  status?: number | '' | null;
  packaging?: string;
  merge?: boolean;
};

function mapAdjustmentItems(items: any[], mergeDefault?: boolean) {
  const mappedItems: StockAdjustmentItem[] = items.map((elem) => {
    return {
      id: elem.pk,
      pk: elem.pk,
      quantity: elem.quantity,
      batch: elem.batch || undefined,
      status: elem.status || undefined,
      packaging: elem.packaging || undefined,
      merge: elem.merge ?? mergeDefault ?? false
    };
  });

  return mappedItems;
}

function stockTransferFields(
  items: any[],
  mergeDefault = false
): ApiFormFieldSet {
  if (!items) {
    return {};
  }

  const records = Object.fromEntries(items.map((item) => [item.pk, item]));

  // Extract all location values from the items
  const locations = [...new Set(items.map((item) => item.location))];

  const fields: ApiFormFieldSet = {
    items: {
      field_type: 'table',
      value: mapAdjustmentItems(items, mergeDefault),
      modelRenderer: (row: TableFieldRowProps) => {
        const record = records[row.item.pk];

        return (
          <StockOperationsRow
            props={row}
            transfer
            changeStatus
            setMax
            transferMerge
            key={row.rowId}
            record={record}
          />
        );
      },
      headers: [
        { title: t`Part` },
        { title: t`Location` },
        { title: t`Batch` },
        { title: t`Stock` },
        { title: t`Move`, style: { width: '200px' } },
        { title: t`Actions` }
      ]
    },
    location: {
      value: locations.length === 1 ? locations[0] : undefined,
      filters: {
        structural: false
      }
    },
    notes: {}
  };
  return fields;
}

function stockReturnFields(items: any[]): ApiFormFieldSet {
  if (!items) {
    return {};
  }

  // Only include items that are currently *not* in stock
  const records = Object.fromEntries(
    items.filter((item) => !item.in_stock).map((item) => [item.pk, item])
  );

  const fields: ApiFormFieldSet = {
    items: {
      field_type: 'table',
      value: mapAdjustmentItems(items),
      modelRenderer: (row: TableFieldRowProps) => {
        const record = records[row.item.pk];

        return (
          <StockOperationsRow
            props={row}
            key={row.rowId}
            record={record}
            transfer
            returnStock
            changeStatus
          />
        );
      },
      headers: [
        { title: t`Part` },
        { title: t`Location` },
        { title: t`Batch` },
        { title: t`Quantity` },
        { title: t`Return`, style: { width: '200px' } },
        { title: t`Actions` }
      ]
    },
    location: {
      field_type: 'related field',
      api_url: apiUrl(ApiEndpoints.stock_location_list),
      model: ModelType.stocklocation,
      required: true,
      filters: {
        structural: false
      }
    },
    merge: {
      field_type: 'boolean',
      label: t`Merge into existing stock`,
      description: t`Merge returned items into existing stock items if possible`,
      value: false
    },
    notes: {
      field_type: 'string',
      label: t`Notes`,
      description: t`Stock transaction notes`
    }
  };

  return fields;
}

function stockRemoveFields(items: any[]): ApiFormFieldSet {
  if (!items) {
    return {};
  }

  // Only include items which are not serialized (serial number field is empty)
  const validItems = items.filter((item) => !item.serial && item.quantity > 0);

  const records = Object.fromEntries(validItems.map((item) => [item.pk, item]));

  const initialValue = mapAdjustmentItems(validItems).map((elem) => {
    return {
      ...elem,
      quantity: 0
    };
  });

  const fields: ApiFormFieldSet = {
    items: {
      field_type: 'table',
      value: initialValue,
      modelRenderer: (row: TableFieldRowProps) => {
        const record = records[row.item.pk];

        return (
          <StockOperationsRow
            props={row}
            setMax
            changeStatus
            add
            key={row.rowId}
            record={record}
          />
        );
      },
      headers: [
        { title: t`Part` },
        { title: t`Location` },
        { title: t`Batch` },
        { title: t`In Stock` },
        { title: t`Remove`, style: { width: '200px' } },
        { title: t`Actions` }
      ]
    },
    notes: {}
  };

  return fields;
}

function stockAddFields(items: any[]): ApiFormFieldSet {
  if (!items) {
    return {};
  }

  // Only include items which are not serialized (serial number field is empty)
  const validItems = items.filter((item) => !item.serial);

  const records = Object.fromEntries(validItems.map((item) => [item.pk, item]));

  const initialValue = mapAdjustmentItems(validItems).map((elem) => {
    return {
      ...elem,
      quantity: 0
    };
  });

  const fields: ApiFormFieldSet = {
    items: {
      field_type: 'table',
      value: initialValue,
      modelRenderer: (row: TableFieldRowProps) => {
        const record = records[row.item.pk];

        return (
          <StockOperationsRow
            changeStatus
            props={row}
            add
            key={row.rowId}
            record={record}
          />
        );
      },
      headers: [
        { title: t`Part` },
        { title: t`Location` },
        { title: t`Batch` },
        { title: t`In Stock` },
        { title: t`Add`, style: { width: '200px' } },
        { title: t`Actions` }
      ]
    },
    notes: {}
  };

  return fields;
}

function stockCountFields(items: any[]): ApiFormFieldSet {
  const records = Object.fromEntries(
    items?.map((item) => [item.pk, item]) ?? []
  );

  const initialValue = items ? mapAdjustmentItems(items) : [];

  // Extract all location values from the items
  const locations = [...new Set(items?.map((item) => item.location))];

  const fields: ApiFormFieldSet = {
    items: {
      field_type: 'table',
      value: initialValue,
      modelRenderer: (row: TableFieldRowProps) => {
        return (
          <StockOperationsRow
            props={row}
            changeStatus
            key={row.rowId}
            record={records[row.item?.pk]}
          />
        );
      },
      headers: [
        { title: t`Part` },
        { title: t`Location` },
        { title: t`Batch` },
        { title: t`In Stock` },
        { title: t`Count`, style: { width: '200px' } },
        { title: t`Actions` }
      ]
    },
    location: {
      value: locations.length === 1 ? locations[0] : undefined,
      filters: {
        structural: false
      }
    },
    notes: {}
  };

  return fields;
}

function stockChangeStatusFields(items: any[]): ApiFormFieldSet {
  if (!items) {
    return {};
  }

  const records = Object.fromEntries(items.map((item) => [item.pk, item]));

  // Extract all status values from the items
  const statusValues = [
    ...new Set(items.map((item) => item.status_custom_key ?? item.status))
  ];

  const fields: ApiFormFieldSet = {
    items: {
      field_type: 'table',
      value: items.map((elem) => {
        return elem.pk;
      }),
      modelRenderer: (row: TableFieldRowProps) => {
        return (
          <StockOperationsRow
            props={row}
            key={row.rowId}
            merge
            record={records[row.item]}
          />
        );
      },
      headers: [
        { title: t`Part` },
        { title: t`Location` },
        { title: t`Batch` },
        { title: t`In Stock` },
        { title: '', style: { width: '50px' } }
      ]
    },
    status: {
      value: statusValues.length === 1 ? statusValues[0] : undefined
    },
    note: {}
  };

  return fields;
}

function stockMergeFields(items: any[]): ApiFormFieldSet {
  if (!items) {
    return {};
  }

  // Only include items which are not serialized (serial number field is empty)
  const validItems = items.filter((item) => !item.serial);

  const records = Object.fromEntries(validItems.map((item) => [item.pk, item]));

  // Extract all non-null location values from the items
  const locationValues = [
    ...new Set(
      validItems.filter((item) => item.location).map((item) => item.location)
    )
  ];

  // Extract all non-null default location values from the items
  const defaultLocationValues = [
    ...new Set(
      validItems
        .filter((item) => item.part_detail?.default_location)
        .map((item) => item.part_detail?.default_location)
    )
  ];

  // Select a default location value
  const defaultLocation =
    locationValues.length === 1
      ? locationValues[0]
      : defaultLocationValues.length === 1
        ? defaultLocationValues[0]
        : undefined;

  const fields: ApiFormFieldSet = {
    items: {
      field_type: 'table',
      value: validItems.map((elem) => {
        return {
          item: elem.pk
        };
      }),
      modelRenderer: (row: TableFieldRowProps) => {
        return (
          <StockOperationsRow
            props={row}
            key={row.rowId}
            merge
            changeStatus
            record={records[row.item.item]}
          />
        );
      },
      headers: [
        { title: t`Part` },
        { title: t`Location` },
        { title: t`Batch` },
        { title: t`In Stock` },
        { title: t`Actions` }
      ]
    },
    location: {
      default: defaultLocation,
      filters: {
        structural: false
      }
    },
    notes: {},
    allow_mismatched_suppliers: {},
    allow_mismatched_status: {}
  };

  return fields;
}

function stockAssignFields(items: any[]): ApiFormFieldSet {
  if (!items) {
    return {};
  }

  const records = Object.fromEntries(items.map((item) => [item.pk, item]));

  const fields: ApiFormFieldSet = {
    items: {
      field_type: 'table',
      value: items.map((elem) => {
        return {
          item: elem.pk
        };
      }),
      modelRenderer: (row: TableFieldRowProps) => {
        return (
          <StockOperationsRow
            props={row}
            key={row.rowId}
            merge
            record={records[row.item.item]}
          />
        );
      },
      headers: [
        { title: t`Part` },
        { title: t`Location` },
        { title: t`Batch` },
        { title: t`In Stock` },
        { title: '', style: { width: '50px' } }
      ]
    },
    customer: {
      filters: {
        is_customer: true
      }
    },
    notes: {}
  };

  return fields;
}

function stockDeleteFields(items: any[]): ApiFormFieldSet {
  if (!items) {
    return {};
  }

  const records = Object.fromEntries(items.map((item) => [item.pk, item]));

  const fields: ApiFormFieldSet = {
    items: {
      field_type: 'table',
      value: items.map((elem) => {
        return elem.pk;
      }),
      modelRenderer: (row: TableFieldRowProps) => {
        const record = records[row.item];

        return (
          <StockOperationsRow
            props={row}
            key={row.rowId}
            merge
            record={record}
          />
        );
      },
      headers: [
        { title: t`Part` },
        { title: t`Location` },
        { title: t`Batch` },
        { title: t`In Stock` },
        { title: '', style: { width: '50px' } }
      ]
    }
  };

  return fields;
}

type apiModalFunc = (props: ApiFormModalProps) => {
  open: () => void;
  close: () => void;
  toggle: () => void;
  modal: JSX.Element;
};

function useStockOperationModal({
  items,
  refresh,
  fieldGenerator,
  endpoint,
  filters,
  title,
  preFormContent,
  successMessage,
  modalFunc = useCreateApiFormModal
}: {
  items?: object;
  filters?: any;
  refresh: () => void;
  fieldGenerator: (items: any[]) => ApiFormFieldSet;
  endpoint: ApiEndpoints;
  title: string;
  preFormContent?: JSX.Element;
  successMessage?: string;
  modalFunc?: apiModalFunc;
}) {
  const [opened, setOpened] = useState<boolean>(false);

  const stockItems = useStockItems({
    opened: opened,
    items: items,
    filters: filters
  });

  // Rebuild the "fields" object
  const fields = useMemo(
    () => fieldGenerator(stockItems),
    [fieldGenerator, stockItems]
  );

  return modalFunc({
    url: endpoint,
    fields: fields,
    preFormContent: preFormContent,
    title: title,
    size: '80%',
    successMessage: successMessage,
    onFormSuccess: () => refresh(),
    onClose: () => setOpened(false),
    onOpen: () => setOpened(true)
  });
}

export function useAddStockItem(props: StockOperationProps) {
  return useStockOperationModal({
    ...props,
    fieldGenerator: stockAddFields,
    endpoint: ApiEndpoints.stock_add,
    title: t`Add Stock`,
    successMessage: t`Stock added`,
    preFormContent: (
      <Alert color='blue'>
        {t`Increase the quantity of the selected stock items by a given amount.`}
      </Alert>
    )
  });
}

export function useRemoveStockItem(props: StockOperationProps) {
  return useStockOperationModal({
    ...props,
    fieldGenerator: stockRemoveFields,
    endpoint: ApiEndpoints.stock_remove,
    title: t`Remove Stock`,
    successMessage: t`Stock removed`,
    preFormContent: (
      <Alert color='blue'>
        {t`Decrease the quantity of the selected stock items by a given amount.`}
      </Alert>
    )
  });
}

export function useTransferStockItem(props: StockOperationProps) {
  const globalSettings = useGlobalSettingsState();

  const fieldGenerator = useCallback(
    (items: any[]) =>
      stockTransferFields(
        items,
        globalSettings.isSet('STOCK_MERGE_ON_TRANSFER')
      ),
    [globalSettings]
  );

  return useStockOperationModal({
    ...props,
    fieldGenerator: fieldGenerator,
    endpoint: ApiEndpoints.stock_transfer,
    title: t`Transfer Stock`,
    successMessage: t`Stock transferred`,
    preFormContent: (
      <Alert color='blue'>
        {t`Transfer selected items to the specified location.`}
      </Alert>
    )
  });
}

export function useReturnStockItem(props: StockOperationProps) {
  return useStockOperationModal({
    ...props,
    fieldGenerator: stockReturnFields,
    endpoint: ApiEndpoints.stock_return,
    title: t`Return Stock`,
    successMessage: t`Stock returned`,
    preFormContent: (
      <Alert color='blue'>
        {t`Return selected items into stock, to the specified location.`}
      </Alert>
    )
  });
}

export function useCountStockItem(props: StockOperationProps) {
  const fieldGenerator = useCallback(
    (items: any[]) => stockCountFields(items),
    []
  );

  return useStockOperationModal({
    ...props,
    fieldGenerator: fieldGenerator,
    endpoint: ApiEndpoints.stock_count,
    title: t`Count Stock`,
    successMessage: t`Stock counted`,
    preFormContent: (
      <Alert color='blue'>
        {t`Count the selected stock items, and adjust the quantity accordingly.`}
      </Alert>
    )
  });
}

export function useChangeStockStatus(props: StockOperationProps) {
  return useStockOperationModal({
    ...props,
    fieldGenerator: stockChangeStatusFields,
    endpoint: ApiEndpoints.stock_change_status,
    title: t`Change Stock Status`,
    successMessage: t`Stock status changed`,
    preFormContent: (
      <Alert color='blue'>
        {t`Change the status of the selected stock items.`}
      </Alert>
    )
  });
}

export function useChangeStockBatchCode(props: StockOperationProps) {
  // Return a common batch code value if all items share the same batch code, otherwise return undefined
  const batchCode = useMemo(() => {
    const batchCodeValues = new Set(
      props.items?.filter((item) => item.batch).map((item) => item.batch)
    );

    if (batchCodeValues.size === 1) {
      return batchCodeValues.values().next().value;
    }

    return undefined;
  }, [props.items]);

  return useBulkEditApiFormModal({
    url: ApiEndpoints.stock_item_list,
    items: props.items?.map((item: any) => item.pk) ?? [],
    title: t`Change Batch Code`,
    preFormContent: (
      <Alert color='blue'>
        {t`Change batch code for the selected stock items`}
      </Alert>
    ),
    fields: {
      batch: {
        value: batchCode
      }
    },
    onFormSuccess: props.refresh
  });
}

export function useMergeStockItem(props: StockOperationProps) {
  return useStockOperationModal({
    ...props,
    fieldGenerator: stockMergeFields,
    endpoint: ApiEndpoints.stock_merge,
    title: t`Merge Stock`,
    successMessage: t`Stock merged`,
    preFormContent: (
      <Alert title={t`Merge Stock Items`} color='yellow'>
        <List>
          <List.Item>{t`Merge operation cannot be reversed`}</List.Item>
          <List.Item>{t`Tracking information may be lost when merging items`}</List.Item>
          <List.Item>{t`Supplier information may be lost when merging items`}</List.Item>
        </List>
      </Alert>
    )
  });
}

export function useAssignStockItem(props: StockOperationProps) {
  // Filter items - only allow 'salable' items
  const items = useMemo(() => {
    return props.items?.filter((item) => item?.part_detail?.salable);
  }, [props.items]);

  return useStockOperationModal({
    ...props,
    items: items,
    fieldGenerator: stockAssignFields,
    endpoint: ApiEndpoints.stock_assign,
    title: t`Assign Stock to Customer`,
    successMessage: t`Stock assigned to customer`
  });
}

export function useDeleteStockItem(props: StockOperationProps) {
  return useStockOperationModal({
    ...props,
    fieldGenerator: stockDeleteFields,
    endpoint: ApiEndpoints.stock_item_list,
    modalFunc: useDeleteApiFormModal,
    title: t`Delete Stock Items`,
    successMessage: t`Stock deleted`,
    preFormContent: (
      <Alert color='red'>
        {t`This operation will permanently delete the selected stock items.`}
      </Alert>
    )
  });
}

export function useStockLocationFields(): ApiFormFieldSet {
  const globalSettings = useGlobalSettingsState();

  const fields: ApiFormFieldSet = {
    parent: {
      description: t`Parent stock location`,
      required: false
    },
    name: {},
    description: {},
    owner: {
      icon: <IconUsersGroup />
    },
    structural: {},
    external: {},
    exclude_from_stock: {},
    custom_icon: {
      field_type: 'icon'
    },
    location_type: {}
  };

  // Ownership of a stock location is only relevant if
  // stock ownership control is enabled
  if (!globalSettings.isSet('STOCK_OWNERSHIP_CONTROL')) {
    delete fields.owner;
  }

  return fields;
}

// Construct a set of fields for
export function useTestResultFields({
  partId,
  itemId,
  templateId,
  editing = false,
  editTemplate = false
}: {
  partId: number;
  itemId: number;
  templateId: number | undefined;
  editing?: boolean;
  editTemplate?: boolean;
}): ApiFormFieldSet {
  // Valid field choices
  const [choices, setChoices] = useState<any[]>([]);

  // Field type for the "value" input
  const [fieldType, setFieldType] = useState<'string' | 'choice'>('string');

  const settings = useGlobalSettingsState();

  const includeTestStation = useMemo(
    () => settings.isSet('TEST_STATION_DATA'),
    [settings]
  );

  return useMemo(() => {
    const fields: ApiFormFieldSet = {
      stock_item: {
        value: itemId,
        hidden: true
      },
      template: {
        disabled: !editTemplate && !!templateId,
        filters: {
          include_inherited: true,
          part: partId
        },
        onValueChange: (value: any, record: any) => {
          // Adjust the type of the "value" field based on the selected template
          if (record?.choices) {
            const _choices: string[] = record.choices.split(',');

            if (_choices.length > 0) {
              setChoices(
                _choices.map((choice) => {
                  return {
                    label: choice.trim(),
                    value: choice.trim()
                  };
                })
              );
              setFieldType('choice');
            } else {
              setChoices([]);
              setFieldType('string');
            }
          } else {
            // No choices defined - this is a free-form text field
            setChoices([]);
            setFieldType('string');
          }
        }
      },
      result: {},
      value: {
        field_type: fieldType,
        choices: fieldType === 'choice' ? choices : undefined
      },
      attachment: {},
      notes: {},
      started_datetime: {
        hidden: !includeTestStation
      },
      finished_datetime: {
        hidden: !includeTestStation
      },
      test_station: {
        hidden: !includeTestStation
      }
    };

    if (editing) {
      // Prevent changing uploaded attachments
      delete fields.attachment;
    }

    return fields;
  }, [
    choices,
    editing,
    editTemplate,
    fieldType,
    partId,
    itemId,
    templateId,
    includeTestStation
  ]);
}

/**
 * Modal form for finding a particular stock item by serial number
 */
export function useFindSerialNumberForm({ partId }: { partId: number }) {
  const navigate = useNavigate();

  return useApiFormModal({
    url: apiUrl(ApiEndpoints.stock_item_list),
    fetchInitialData: false,
    method: 'GET',
    title: t`Find Serial Number`,
    fields: {
      serial: {},
      part_tree: {
        value: partId,
        hidden: true,
        field_type: 'integer'
      }
    },
    checkClose: (data, form) => {
      if (!data || data?.length == 0) {
        form.setError('serial', { message: t`No matching items` });
        return false;
      }

      if (data.length > 1) {
        form.setError('serial', {
          message: t`Multiple matching items`
        });
        return false;
      }

      if (data[0].pk) {
        return true;
      } else {
        form.setError('serial', {
          message: t`Invalid response from server`
        });
        return false;
      }
    },
    onFormSuccess: (data) => {
      if (data.length == 1 && data[0].pk) {
        navigate(getDetailUrl(ModelType.stockitem, data[0].pk));
      }
    }
  });
}
