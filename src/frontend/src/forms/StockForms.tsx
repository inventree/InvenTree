import { t } from '@lingui/macro';
import { Flex, Group, Skeleton, Table, Text } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { modals } from '@mantine/modals';
import { useQuery, useSuspenseQuery } from '@tanstack/react-query';
import { Suspense, useMemo, useState } from 'react';

import { api } from '../App';
import { ActionButton } from '../components/buttons/ActionButton';
import RemoveRowButton from '../components/buttons/RemoveRowButton';
import { StandaloneField } from '../components/forms/StandaloneField';
import {
  ApiFormAdjustFilterType,
  ApiFormFieldSet
} from '../components/forms/fields/ApiFormField';
import {
  TableFieldExtraRow,
  TableFieldRowProps
} from '../components/forms/fields/TableField';
import { Thumbnail } from '../components/images/Thumbnail';
import { StylishText } from '../components/items/StylishText';
import { StatusRenderer } from '../components/render/StatusRenderer';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { ModelType } from '../enums/ModelType';
import { InvenTreeIcon } from '../functions/icons';
import {
  ApiFormModalProps,
  useCreateApiFormModal,
  useDeleteApiFormModal
} from '../hooks/UseForm';
import {
  useBatchCodeGenerator,
  useSerialNumberGenerator
} from '../hooks/UseGenerator';
import { apiUrl } from '../states/ApiState';
import { useGlobalSettingsState } from '../states/SettingsState';

/**
 * Construct a set of fields for creating / editing a StockItem instance
 */
export function useStockFields({
  create = false
}: {
  create: boolean;
}): ApiFormFieldSet {
  const [part, setPart] = useState<number | null>(null);
  const [supplierPart, setSupplierPart] = useState<number | null>(null);

  const [batchCode, setBatchCode] = useState<string>('');
  const [serialNumbers, setSerialNumbers] = useState<string>('');

  const [trackable, setTrackable] = useState<boolean>(false);

  const batchGenerator = useBatchCodeGenerator((value: any) => {
    if (!batchCode) {
      setBatchCode(value);
    }
  });

  const serialGenerator = useSerialNumberGenerator((value: any) => {
    if (!serialNumbers && create && trackable) {
      setSerialNumbers(value);
    }
  });

  return useMemo(() => {
    const fields: ApiFormFieldSet = {
      part: {
        value: part,
        disabled: !create,
        onValueChange: (value, record) => {
          setPart(value);
          // TODO: implement remaining functionality from old stock.py

          setTrackable(record.trackable ?? false);

          batchGenerator.update({ part: value });
          serialGenerator.update({ part: value });

          if (!record.trackable) {
            setSerialNumbers('');
          }

          // Clear the 'supplier_part' field if the part is changed
          setSupplierPart(null);
        }
      },
      supplier_part: {
        // TODO: icon
        value: supplierPart,
        onValueChange: (value) => {
          setSupplierPart(value);
        },
        filters: {
          part_detail: true,
          supplier_detail: true,
          ...(part ? { part } : {})
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
        }
      },
      serial_numbers: {
        field_type: 'string',
        label: t`Serial Numbers`,
        description: t`Enter serial numbers for new stock (or leave blank)`,
        required: false,
        disabled: !trackable,
        hidden: !create,
        value: serialNumbers,
        onValueChange: (value) => setSerialNumbers(value)
      },
      serial: {
        hidden: create
        // TODO: icon
      },
      batch: {
        // TODO: icon
        value: batchCode,
        onValueChange: (value) => setBatchCode(value)
      },
      status_custom_key: {
        label: t`Stock Status`
      },
      expiry_date: {
        // TODO: icon
      },
      purchase_price: {
        // TODO: icon
      },
      purchase_price_currency: {
        // TODO: icon
      },
      packaging: {
        // TODO: icon,
      },
      link: {
        // TODO: icon
      },
      owner: {
        // TODO: icon
      },
      delete_on_deplete: {}
    };

    // TODO: Handle custom field management based on provided options
    // TODO: refer to stock.py in original codebase

    return fields;
  }, [part, supplierPart, batchCode, serialNumbers, trackable, create]);
}

/**
 * Launch a form to create a new StockItem instance
 */
export function useCreateStockItem() {
  const fields = useStockFields({ create: true });

  return useCreateApiFormModal({
    url: ApiEndpoints.stock_item_list,
    fields: fields,
    title: t`Add Stock Item`
  });
}

function StockItemDefaultMove({
  stockItem,
  value
}: {
  stockItem: any;
  value: any;
}) {
  const { data } = useSuspenseQuery({
    queryKey: [
      'location',
      stockItem.part_detail.default_location ??
        stockItem.part_detail.category_default_location
    ],
    queryFn: async () => {
      const url = apiUrl(
        ApiEndpoints.stock_location_list,
        stockItem.part_detail.default_location ??
          stockItem.part_detail.category_default_location
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
    <Flex gap="sm" justify="space-evenly" align="center">
      <Flex gap="sm" direction="column" align="center">
        <Text>
          {value} x {stockItem.part_detail.name}
        </Text>
        <Thumbnail
          src={stockItem.part_detail.thumbnail}
          size={80}
          align="center"
        />
      </Flex>
      <Flex direction="column" gap="sm" align="center">
        <Text>{stockItem.location_detail.pathstring}</Text>
        <InvenTreeIcon icon="arrow_down" />
        <Suspense fallback={<Skeleton width="150px" />}>
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
    title: <StylishText>Confirm Stock Transfer</StylishText>,
    children: <StockItemDefaultMove stockItem={stockItem} value={value} />,
    onConfirm: () => {
      if (
        stockItem.location === stockItem.part_detail.default_location ||
        stockItem.location === stockItem.part_detail.category_default_location
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
            stockItem.part_detail.default_location ??
            stockItem.part_detail.category_default_location
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
  add = false,
  setMax = false,
  merge = false,
  record
}: {
  props: TableFieldRowProps;
  transfer?: boolean;
  add?: boolean;
  setMax?: boolean;
  merge?: boolean;
  record?: any;
}) {
  const [quantity, setQuantity] = useState<StockItemQuantity>(
    add ? 0 : props.item?.quantity ?? 0
  );

  const removeAndRefresh = () => {
    props.removeFn(props.idx);
  };

  const [packagingOpen, packagingHandlers] = useDisclosure(false, {
    onOpen: () => {
      if (transfer) {
        props.changeFn(props.idx, 'packaging', record?.packaging || undefined);
      }
    },
    onClose: () => {
      if (transfer) {
        props.changeFn(props.idx, 'packaging', undefined);
      }
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
          <Flex gap="sm" align="center">
            <Thumbnail
              size={40}
              src={record.part_detail?.thumbnail}
              align="center"
            />
            <div>{record.part_detail?.name}</div>
          </Flex>
        </Table.Td>
        <Table.Td>
          {record.location ? record.location_detail?.pathstring : '-'}
        </Table.Td>
        <Table.Td>
          <Group grow justify="space-between" wrap="nowrap">
            <Text>{stockString}</Text>
            <StatusRenderer status={record.status} type={ModelType.stockitem} />
          </Group>
        </Table.Td>
        {!merge && (
          <Table.Td>
            <StandaloneField
              fieldName="quantity"
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
          <Flex gap="3px">
            {transfer && (
              <ActionButton
                onClick={() =>
                  moveToDefault(record, props.item.quantity, removeAndRefresh)
                }
                icon={<InvenTreeIcon icon="default_location" />}
                tooltip={t`Move to default location`}
                tooltipAlignment="top"
                disabled={
                  !record.part_detail?.default_location &&
                  !record.part_detail?.category_default_location
                }
              />
            )}
            {transfer && (
              <ActionButton
                size="sm"
                icon={<InvenTreeIcon icon="packaging" />}
                tooltip={t`Adjust Packaging`}
                onClick={() => packagingHandlers.toggle()}
                variant={packagingOpen ? 'filled' : 'transparent'}
              />
            )}
            <RemoveRowButton onClick={() => props.removeFn(props.idx)} />
          </Flex>
        </Table.Td>
      </Table.Tr>
      {transfer && (
        <TableFieldExtraRow
          visible={transfer && packagingOpen}
          onValueChange={(value: any) => {
            props.changeFn(props.idx, 'packaging', value || undefined);
          }}
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
            setMax
            key={record.pk}
            record={record}
          />
        );
      },
      headers: [t`Part`, t`Location`, t`In Stock`, t`Move`, t`Actions`]
    },
    location: {
      filters: {
        structural: false
      }
      // TODO: icon
    },
    notes: {}
  };
  return fields;
}

function stockRemoveFields(items: any[]): ApiFormFieldSet {
  if (!items) {
    return {};
  }

  const records = Object.fromEntries(items.map((item) => [item.pk, item]));

  const fields: ApiFormFieldSet = {
    items: {
      field_type: 'table',
      value: mapAdjustmentItems(items),
      modelRenderer: (row: TableFieldRowProps) => {
        const record = records[row.item.pk];

        return (
          <StockOperationsRow
            props={row}
            setMax
            add
            key={record.pk}
            record={record}
          />
        );
      },
      headers: [t`Part`, t`Location`, t`In Stock`, t`Remove`, t`Actions`]
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

  const fields: ApiFormFieldSet = {
    items: {
      field_type: 'table',
      value: mapAdjustmentItems(items),
      modelRenderer: (row: TableFieldRowProps) => {
        const record = records[row.item.pk];

        return (
          <StockOperationsRow props={row} add key={record.pk} record={record} />
        );
      },
      headers: [t`Part`, t`Location`, t`In Stock`, t`Add`, t`Actions`]
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

  const fields: ApiFormFieldSet = {
    items: {
      field_type: 'table',
      value: mapAdjustmentItems(items),
      modelRenderer: (row: TableFieldRowProps) => {
        return (
          <StockOperationsRow
            props={row}
            key={row.item.pk}
            record={records[row.item.pk]}
          />
        );
      },
      headers: [t`Part`, t`Location`, t`In Stock`, t`Count`, t`Actions`]
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
      headers: [t`Part`, t`Location`, t`In Stock`, t`Actions`]
    },
    status: {},
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
            record={records[row.item.item]}
          />
        );
      },
      headers: [t`Part`, t`Location`, t`In Stock`, t`Actions`]
    },
    location: {
      default: items[0]?.part_detail.default_location,
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
      headers: [t`Part`, t`Location`, t`In Stock`, t`Actions`]
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
      headers: [t`Part`, t`Location`, t`In Stock`, t`Actions`]
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

function stockOperationModal({
  items,
  pk,
  model,
  refresh,
  fieldGenerator,
  endpoint,
  filters,
  title,
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
  modalFunc?: apiModalFunc;
}) {
  const baseParams: any = {
    part_detail: true,
    location_detail: true,
    cascade: false
  };

  const params = useMemo(() => {
    let query_params: any = {
      ...baseParams,
      ...(filters ?? {})
    };

    query_params[model] =
      pk === undefined && model === 'location' ? 'null' : pk;

    return query_params;
  }, [baseParams, filters, model, pk]);

  const { data } = useQuery({
    queryKey: ['stockitems', model, pk, items, params],
    queryFn: async () => {
      if (items) {
        return Array.isArray(items) ? items : [items];
      }
      const url = apiUrl(ApiEndpoints.stock_item_list);

      return api
        .get(url, {
          params: params
        })
        .then((response) => {
          if (response.status === 200) {
            return response.data;
          }
        })
        .catch(() => {
          return null;
        });
    }
  });

  const fields = useMemo(() => {
    return fieldGenerator(data);
  }, [data]);

  return modalFunc({
    url: endpoint,
    fields: fields,
    title: title,
    size: '80%',
    onFormSuccess: () => refresh()
  });
}

export type StockOperationProps = {
  items?: object;
  pk?: number;
  filters?: any;
  model: ModelType.stockitem | 'location' | ModelType.part;
  refresh: () => void;
};

export function useAddStockItem(props: StockOperationProps) {
  return stockOperationModal({
    ...props,
    fieldGenerator: stockAddFields,
    endpoint: ApiEndpoints.stock_add,
    title: t`Add Stock`
  });
}

export function useRemoveStockItem(props: StockOperationProps) {
  return stockOperationModal({
    ...props,
    fieldGenerator: stockRemoveFields,
    endpoint: ApiEndpoints.stock_remove,
    title: t`Remove Stock`
  });
}

export function useTransferStockItem(props: StockOperationProps) {
  return stockOperationModal({
    ...props,
    fieldGenerator: stockTransferFields,
    endpoint: ApiEndpoints.stock_transfer,
    title: t`Transfer Stock`
  });
}

export function useCountStockItem(props: StockOperationProps) {
  return stockOperationModal({
    ...props,
    fieldGenerator: stockCountFields,
    endpoint: ApiEndpoints.stock_count,
    title: t`Count Stock`
  });
}

export function useChangeStockStatus(props: StockOperationProps) {
  return stockOperationModal({
    ...props,
    fieldGenerator: stockChangeStatusFields,
    endpoint: ApiEndpoints.stock_change_status,
    title: t`Change Stock Status`
  });
}

export function useMergeStockItem(props: StockOperationProps) {
  return stockOperationModal({
    ...props,
    fieldGenerator: stockMergeFields,
    endpoint: ApiEndpoints.stock_merge,
    title: t`Merge Stock`
  });
}

export function useAssignStockItem(props: StockOperationProps) {
  return stockOperationModal({
    ...props,
    fieldGenerator: stockAssignFields,
    endpoint: ApiEndpoints.stock_assign,
    title: `Assign Stock to Customer`
  });
}

export function useDeleteStockItem(props: StockOperationProps) {
  return stockOperationModal({
    ...props,
    fieldGenerator: stockDeleteFields,
    endpoint: ApiEndpoints.stock_item_list,
    modalFunc: useDeleteApiFormModal,
    title: t`Delete Stock Items`
  });
}

export function stockLocationFields(): ApiFormFieldSet {
  let fields: ApiFormFieldSet = {
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
    let fields: ApiFormFieldSet = {
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
            let _choices: string[] = record.choices.split(',');

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
