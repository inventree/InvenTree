import { t } from '@lingui/macro';
import { Flex, NumberInput, Skeleton, Text } from '@mantine/core';
import { modals } from '@mantine/modals';
import { useQuery, useSuspenseQuery } from '@tanstack/react-query';
import { Suspense, useCallback, useMemo, useState } from 'react';

import { api } from '../App';
import { ActionButton } from '../components/buttons/ActionButton';
import { ApiFormFieldSet } from '../components/forms/fields/ApiFormField';
import { Thumbnail } from '../components/images/Thumbnail';
import { StylishText } from '../components/items/StylishText';
import { StatusRenderer } from '../components/render/StatusRenderer';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { ModelType } from '../enums/ModelType';
import { InvenTreeIcon } from '../functions/icons';
import { useCreateApiFormModal, useEditApiFormModal } from '../hooks/UseForm';
import { apiUrl } from '../states/ApiState';

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

  return useMemo(() => {
    const fields: ApiFormFieldSet = {
      part: {
        value: part,
        hidden: !create,
        onValueChange: (change) => {
          setPart(change);
          // TODO: implement remaining functionality from old stock.py

          // Clear the 'supplier_part' field if the part is changed
          setSupplierPart(null);
        }
      },
      supplier_part: {
        // TODO: icon
        value: supplierPart,
        onValueChange: setSupplierPart,
        filters: {
          part_detail: true,
          supplier_detail: true,
          ...(part ? { part } : {})
        }
      },
      use_pack_size: {
        hidden: !create,
        description: t`Add given quantity as packs instead of individual items`
      },
      location: {
        hidden: !create,
        filters: {
          structural: false
        }
        // TODO: icon
      },
      quantity: {
        hidden: !create,
        description: t`Enter initial quantity for this stock item`
      },
      serial_numbers: {
        // TODO: icon
        field_type: 'string',
        label: t`Serial Numbers`,
        description: t`Enter serial numbers for new stock (or leave blank)`,
        required: false,
        hidden: !create
      },
      serial: {
        hidden: create
        // TODO: icon
      },
      batch: {
        // TODO: icon
      },
      status: {},
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
  }, [part, supplierPart]);
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

/**
 * Launch a form to edit an existing StockItem instance
 * @param item : primary key of the StockItem to edit
 */
export function useEditStockItem({
  item_id,
  callback
}: {
  item_id: number;
  callback?: () => void;
}) {
  const fields = useStockFields({ create: false });

  return useEditApiFormModal({
    url: ApiEndpoints.stock_item_list,
    pk: item_id,
    fields: fields,
    title: t`Edit Stock Item`,
    successMessage: t`Stock item updated`,
    onFormSuccess: callback
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
    queryKey: ['location', stockItem.part_detail.default_location],
    queryFn: async () => {
      const url = apiUrl(
        ApiEndpoints.stock_location_list,
        stockItem.part_detail.default_location
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

function moveToDefault(stockItem: any, value: any, refresh: any) {
  modals.openConfirmModal({
    title: <StylishText>Confirm Stock Transfer</StylishText>,
    children: <StockItemDefaultMove stockItem={stockItem} value={value} />,
    onConfirm: () => {
      if (stockItem.location === stockItem.part_detail.default_location) {
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
          location: stockItem.part_detail.default_location
        })
        .then((response) => {
          refresh();
          return response.data;
        })
        .catch((e) => {
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
  input,
  refresh
}: {
  input: StockRow;
  refresh: () => void;
}) {
  const item = input.item;

  const [value, setValue] = useState<StockItemQuantity>(item.quantity);

  const onChange = useCallback(
    (value: any) => {
      setValue(value);
      input.changeFn(input.idx, 'quantity', value);
    },
    [item]
  );

  const removeAndRefresh = () => {
    input.removeFn(input.idx);
    refresh();
  };

  return (
    <tr>
      <td>
        <Flex gap="sm" align="center">
          <Thumbnail
            size={40}
            src={item.obj.part_detail.thumbnail}
            align="center"
          />
          <div>{item.obj.part_detail.name}</div>
        </Flex>
      </td>
      <td>{item.obj.location ? item.obj.location_detail.pathstring : '-'}</td>
      <td>
        <Flex align="center" gap="xs">
          <Text>{item.obj.quantity}</Text>
          <StatusRenderer status={item.obj.status} type={ModelType.stockitem} />
        </Flex>
      </td>
      <td>
        <NumberInput
          value={value}
          onChange={onChange}
          max={item.obj.quantity}
          min={0}
          style={{ maxWidth: '100px' }}
        />
      </td>
      <td>
        <Flex gap="3px">
          <ActionButton
            onClick={() => moveToDefault(item.obj, value, removeAndRefresh)}
            icon={<InvenTreeIcon icon="default_location" />}
            tooltip="Move to default location"
            tooltipAlignment="top"
            disabled={!item.obj.part_detail.default_location}
          />
          <ActionButton
            onClick={() => input.removeFn(input.idx)}
            icon={<InvenTreeIcon icon="square_x" />}
            tooltip="Remove from list"
            tooltipAlignment="top"
            color="red"
          />
        </Flex>
      </td>
    </tr>
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

function stockTransferFields(item: any[]): ApiFormFieldSet {
  if (!item) {
    return {};
  }

  const mappedItems: StockAdjustmentItemWithRecord[] = item.map((elem) => {
    return {
      pk: elem.pk,
      quantity: elem.quantity,
      batch: elem.batch,
      status: elem.status,
      packaging: elem.packaging,
      obj: elem
    };
  });

  const fields: ApiFormFieldSet = {
    items: {
      field_type: 'table',
      value: mappedItems,
      modelRenderer: (val) => {
        return (
          <StockOperationsRow
            input={val}
            refresh={() => {
              return;
            }}
            key={val.item.pk}
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

function stockRemoveFields(item: any[]): ApiFormFieldSet {
  if (!item) {
    return {};
  }

  const mappedItems: StockAdjustmentItem[] = item.map((elem) => {
    return {
      pk: elem.pk,
      quantity: elem.quantity,
      batch: elem.batch,
      status: elem.status,
      packaging: elem.packaging,
      obj: elem
    };
  });

  const fields: ApiFormFieldSet = {
    items: {
      field_type: 'table',
      value: mappedItems,
      modelRenderer: (val) => {
        return <></>;
      },
      headers: [t`Part`, t`Location`, t`In Stock`, t`Remove`, t`Actions`]
    },
    notes: {}
  };

  return fields;
}

export function useTransferStockItem({
  item,
  model,
  refresh
}: {
  item: any;
  model: ModelType | string;
  refresh: () => void;
}) {
  const params: any = {
    part_detail: true,
    location_detail: true,
    cascade: false
  };
  params[model] = item;
  const { data } = useQuery({
    queryKey: ['stockitems', model, item],
    queryFn: async () => {
      if (model === ModelType.stockitem) {
        return Array.isArray(item) ? item : [item];
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
    return stockTransferFields(data);
  }, [data]);

  return useCreateApiFormModal({
    url: ApiEndpoints.stock_transfer,
    fields: fields,
    title: 'Transfer Stock',
    onFormSuccess: () => refresh()
  });
}

export function stockLocationFields({}: {}): ApiFormFieldSet {
  let fields: ApiFormFieldSet = {
    parent: {
      description: t`Parent stock location`,
      required: false
    },
    name: {},
    description: {},
    structural: {},
    external: {},
    location_type: {}
  };

  return fields;
}
