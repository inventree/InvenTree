import { t } from '@lingui/core/macro';
import {
  Alert,
  Flex,
  Group,
  List,
  Skeleton,
  Stack,
  Table,
  Text
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { modals } from '@mantine/modals';
import {
  IconCalendarExclamation,
  IconCoins,
  IconCurrencyDollar,
  IconLink,
  IconPackage,
  IconUsersGroup
} from '@tabler/icons-react';
import { useQuery, useSuspenseQuery } from '@tanstack/react-query';
import { type JSX, Suspense, useEffect, useMemo, useState } from 'react';

import { ActionButton } from '@lib/components/ActionButton';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import dayjs from 'dayjs';
import { useNavigate } from 'react-router-dom';
import { api } from '../App';
import RemoveRowButton from '../components/buttons/RemoveRowButton';
import { StandaloneField } from '../components/forms/StandaloneField';

import { apiUrl } from '@lib/functions/Api';
import { getDetailUrl } from '@lib/functions/Navigation';
import type {
  ApiFormAdjustFilterType,
  ApiFormFieldChoice,
  ApiFormFieldSet,
  ApiFormModalProps,
  StockOperationProps
} from '@lib/types/Forms';
import {
  TableFieldExtraRow,
  type TableFieldRowProps
} from '../components/forms/fields/TableField';
import { Thumbnail } from '../components/images/Thumbnail';
import { StylishText } from '../components/items/StylishText';
import { StatusRenderer } from '../components/render/StatusRenderer';
import { RenderStockLocation } from '../components/render/Stock';
import { InvenTreeIcon } from '../functions/icons';
import {
  useApiFormModal,
  useCreateApiFormModal,
  useDeleteApiFormModal
} from '../hooks/UseForm';
import {
  useBatchCodeGenerator,
  useSerialNumberGenerator
} from '../hooks/UseGenerator';
import { useGlobalSettingsState } from '../states/SettingsStates';
import { StatusFilterOptions } from '../tables/Filter';

/**
 * Construct a set of fields for creating / editing a StockItem instance
 */
export function useStockFields({
  partId,
  stockItem,
  create = false,
  supplierPartId,
  pricing,
  modalId
}: {
  partId?: number;
  stockItem?: any;
  modalId: string;
  create: boolean;
  supplierPartId?: number;
  pricing?: { [priceBreak: number]: [number, string] };
}): ApiFormFieldSet {
  const globalSettings = useGlobalSettingsState();

  // Keep track of the "part" instance
  const [partInstance, setPartInstance] = useState<any>({});

  const [supplierPart, setSupplierPart] = useState<number | null>(
    supplierPartId ?? null
  );

  const [expiryDate, setExpiryDate] = useState<string | null>(null);
  const [quantity, setQuantity] = useState<number | null>(null);
  const [purchasePrice, setPurchasePrice] = useState<number | null>(null);
  const [purchasePriceCurrency, setPurchasePriceCurrency] = useState<
    string | null
  >(null);

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

  // Update pricing when quantity changes
  useEffect(() => {
    if (quantity === null || quantity === undefined || !pricing) return;

    // Find the highest price break that is less than or equal to the quantity
    const priceBreak = Object.entries(pricing)
      .sort(([a], [b]) => Number.parseInt(b) - Number.parseInt(a))
      .find(([br]) => quantity >= Number.parseInt(br));

    if (priceBreak) {
      setPurchasePrice(priceBreak[1][0]);
      setPurchasePriceCurrency(priceBreak[1][1]);
    }
  }, [pricing, quantity]);

  // Set the supplier part if provided
  useEffect(() => {
    if (supplierPartId && !supplierPart) setSupplierPart(supplierPartId);
  }, [partInstance, supplierPart, supplierPartId]);

  // Set default currency from global settings
  useEffect(() => {
    setPurchasePriceCurrency(
      globalSettings.getSetting('INVENTREE_DEFAULT_CURRENCY')
    );
  }, [globalSettings]);

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
        onValueChange: (value) => {
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
          setQuantity(value);
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
        label: t`Stock Status`
      },
      expiry_date: {
        icon: <IconCalendarExclamation />,
        hidden: !globalSettings.isSet('STOCK_ENABLE_EXPIRY'),
        value: expiryDate,
        onValueChange: (value) => {
          setExpiryDate(value);
        }
      },
      purchase_price: {
        icon: <IconCurrencyDollar />,
        value: purchasePrice,
        onValueChange: (value) => {
          setPurchasePrice(value);
        }
      },
      purchase_price_currency: {
        icon: <IconCoins />,
        default: globalSettings.getSetting('INVENTREE_DEFAULT_CURRENCY'),
        value: purchasePriceCurrency,
        onValueChange: (value) => {
          setPurchasePriceCurrency(value);
        }
      },
      packaging: {
        icon: <IconPackage />
      },
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

    return fields;
  }, [
    stockItem,
    expiryDate,
    partInstance,
    partId,
    globalSettings,
    supplierPart,
    create,
    supplierPartId,
    purchasePrice,
    purchasePriceCurrency,
    serialGenerator.result,
    batchGenerator.result,
    create
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
    title: t`Add Stock Item`
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
          part: selectedPart ? selectedPart : undefined
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
  refresh: () => void
) {
  modals.openConfirmModal({
    title: <StylishText>{t`Confirm Stock Transfer`}</StylishText>,
    children: <StockItemDefaultMove stockItem={stockItem} value={value} />,
    onConfirm: () => {
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
          location:
            stockItem.part_detail?.default_location ??
            stockItem.part_detail?.category_default_location
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

type StockAdjustmentItemWithRecord = {
  obj: any;
} & StockAdjustmentItem;

type TableFieldRefreshFn = (idx: number) => void;
type TableFieldChangeFn = (idx: number, key: string, value: any) => void;

type StockRow = {
  item: StockAdjustmentItemWithRecord;
  idx: number;
  changeFn: TableFieldChangeFn;
  removeFn: TableFieldRefreshFn;
};

function StockOperationsRow({
  props,
  transfer = false,
  changeStatus = false,
  add = false,
  setMax = false,
  merge = false,
  record
}: {
  props: TableFieldRowProps;
  transfer?: boolean;
  changeStatus?: boolean;
  add?: boolean;
  setMax?: boolean;
  merge?: boolean;
  record?: any;
}) {
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

  const removeAndRefresh = () => {
    props.removeFn(props.idx);
  };

  const callChangeFn = (idx: number, key: string, value: any) => {
    setTimeout(() => props.changeFn(idx, key, value), 0);
  };

  const [packagingOpen, packagingHandlers] = useDisclosure(false, {
    onOpen: () => {
      if (transfer) {
        callChangeFn(props.idx, 'packaging', record?.packaging || undefined);
      }
    },
    onClose: () => {
      if (transfer) {
        callChangeFn(props.idx, 'packaging', undefined);
      }
    }
  });

  const [statusOpen, statusHandlers] = useDisclosure(false, {
    onOpen: () => {
      setStatus(record?.status_custom_key || record?.status || undefined);
      props.changeFn(props.idx, 'status', record?.status || undefined);
    },
    onClose: () => {
      setStatus(undefined);
      callChangeFn(props.idx, 'status', undefined);
    }
  });

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
    <div>{t`Loading...`}</div>
  ) : (
    <>
      <Table.Tr>
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
              status={record.status_custom_key}
              type={ModelType.stockitem}
            />
          </Group>
        </Table.Td>
        {!merge && (
          <Table.Td>
            <StandaloneField
              fieldName='quantity'
              fieldDefinition={{
                field_type: 'number',
                value: quantity,
                onValueChange: (value: any) => {
                  setQuantity(value);
                  props.changeFn(props.idx, 'quantity', value);
                }
              }}
              error={props.rowErrors?.quantity?.message}
            />
          </Table.Td>
        )}
        <Table.Td>
          <Flex gap='3px'>
            {transfer && (
              <ActionButton
                onClick={() =>
                  moveToDefault(record, props.item.quantity, removeAndRefresh)
                }
                icon={<InvenTreeIcon icon='default_location' />}
                tooltip={t`Move to default location`}
                tooltipAlignment='top'
                disabled={
                  !record.part_detail?.default_location &&
                  !record.part_detail?.category_default_location
                }
              />
            )}
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
            <RemoveRowButton onClick={() => props.removeFn(props.idx)} />
          </Flex>
        </Table.Td>
      </Table.Tr>
      {changeStatus && (
        <TableFieldExtraRow
          visible={statusOpen}
          onValueChange={(value: any) => {
            setStatus(value);
            props.changeFn(props.idx, 'status', value || undefined);
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
            props.changeFn(props.idx, 'packaging', value || undefined);
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
};

function mapAdjustmentItems(items: any[]) {
  const mappedItems: StockAdjustmentItemWithRecord[] = items.map((elem) => {
    return {
      pk: elem.pk,
      quantity: elem.quantity,
      batch: elem.batch || undefined,
      status: elem.status || undefined,
      packaging: elem.packaging || undefined,
      obj: elem
    };
  });

  return mappedItems;
}

function stockTransferFields(items: any[]): ApiFormFieldSet {
  if (!items) {
    return {};
  }

  const records = Object.fromEntries(items.map((item) => [item.pk, item]));

  // Extract all location values from the items
  const locations = [...new Set(items.map((item) => item.location))];

  const fields: ApiFormFieldSet = {
    items: {
      field_type: 'table',
      value: mapAdjustmentItems(items),
      modelRenderer: (row: TableFieldRowProps) => {
        const record = records[row.item.pk];

        return (
          <StockOperationsRow
            props={row}
            transfer
            changeStatus
            setMax
            key={record.pk}
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
            key={record.pk}
            record={record}
            transfer
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
      filters: {
        structural: false
      }
    },
    merge: {},
    notes: {}
  };

  return fields;
}

function stockRemoveFields(items: any[]): ApiFormFieldSet {
  if (!items) {
    return {};
  }

  const records = Object.fromEntries(items.map((item) => [item.pk, item]));

  const initialValue = mapAdjustmentItems(items).map((elem) => {
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
            key={record.pk}
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

  const records = Object.fromEntries(items.map((item) => [item.pk, item]));

  const initialValue = mapAdjustmentItems(items).map((elem) => {
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
            key={record.pk}
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
  if (!items) {
    return {};
  }

  const records = Object.fromEntries(items.map((item) => [item.pk, item]));

  const initialValue = mapAdjustmentItems(items);

  const fields: ApiFormFieldSet = {
    items: {
      field_type: 'table',
      value: initialValue,
      modelRenderer: (row: TableFieldRowProps) => {
        return (
          <StockOperationsRow
            props={row}
            changeStatus
            key={row.item.pk}
            record={records[row.item.pk]}
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
            key={row.item}
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

  const records = Object.fromEntries(items.map((item) => [item.pk, item]));

  const fields: ApiFormFieldSet = {
    items: {
      field_type: 'table',
      value: items.map((elem) => {
        return {
          item: elem.pk,
          obj: elem
        };
      }),
      modelRenderer: (row: TableFieldRowProps) => {
        return (
          <StockOperationsRow
            props={row}
            key={row.item.item}
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
      default: items[0]?.part_detail?.default_location,
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
          item: elem.pk,
          obj: elem
        };
      }),
      modelRenderer: (row: TableFieldRowProps) => {
        return (
          <StockOperationsRow
            props={row}
            key={row.item.item}
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
            key={record.pk}
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
  pk,
  model,
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
  pk?: number;
  filters?: any;
  model: ModelType | string;
  refresh: () => void;
  fieldGenerator: (items: any[]) => ApiFormFieldSet;
  endpoint: ApiEndpoints;
  title: string;
  preFormContent?: JSX.Element;
  successMessage?: string;
  modalFunc?: apiModalFunc;
}) {
  const baseParams: any = {
    part_detail: true,
    location_detail: true,
    cascade: false
  };

  const params = useMemo(() => {
    const query_params: any = {
      ...baseParams,
      ...(filters ?? {})
    };

    query_params[model] =
      pk === undefined && model === 'location' ? 'null' : pk;

    return query_params;
  }, [baseParams, filters, model, pk]);

  const [opened, setOpened] = useState<boolean>(false);

  const { data } = useQuery({
    queryKey: ['stockitems', opened, model, pk, items, params],
    queryFn: async () => {
      if (items) {
        // If a list of items is provided, use that directly
        return Array.isArray(items) ? items : [items];
      }

      if (!pk || !opened) {
        return [];
      }

      const url = apiUrl(ApiEndpoints.stock_item_list);

      return api
        .get(url, {
          params: params
        })
        .then((response) => response.data ?? []);
    }
  });

  const fields = useMemo(() => {
    return fieldGenerator(data);
  }, [data]);

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
  return useStockOperationModal({
    ...props,
    fieldGenerator: stockTransferFields,
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
  return useStockOperationModal({
    ...props,
    fieldGenerator: stockCountFields,
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

export function stockLocationFields(): ApiFormFieldSet {
  const fields: ApiFormFieldSet = {
    parent: {
      description: t`Parent stock location`,
      required: false
    },
    name: {},
    description: {},
    structural: {},
    external: {},
    custom_icon: {
      field_type: 'icon'
    },
    location_type: {}
  };

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
export function useFindSerialNumberForm({
  partId
}: {
  partId: number;
}) {
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
