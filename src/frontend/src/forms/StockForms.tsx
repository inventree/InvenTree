import { t } from '@lingui/macro';
import {
  Button,
  NumberInput,
  Paper,
  Skeleton,
  Table,
  Text,
  Tooltip
} from '@mantine/core';
import { modals } from '@mantine/modals';
import { useSuspenseQuery } from '@tanstack/react-query';
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

function StockOperationsRow({
  input,
  refresh
}: {
  input: any;
  refresh: () => void;
}) {
  const item = input.item;

  const [value, setValue] = useState<number | ''>(item.quantity);
  const { data } = useSuspenseQuery({
    queryKey: ['location', item.obj.part_detail.default_location],
    queryFn: async () => {
      const url = apiUrl(
        ApiEndpoints.stock_location_list,
        item.obj.part_detail.default_location
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

  function _moveToDefault() {
    modals.openConfirmModal({
      title: <StylishText>Confirm Stock Transfer</StylishText>,
      children: (
        <div
          style={{
            display: 'flex',
            gap: '10px',
            alignItems: 'center',
            justifyContent: 'space-evenly'
          }}
        >
          <Paper
            style={{
              display: 'flex',
              gap: '10px',
              flexDirection: 'column',
              alignItems: 'center',
              alignContent: 'space-between'
            }}
          >
            <Text>
              {value} x {item.obj.part_detail.name}
            </Text>
            <Thumbnail
              src={item.obj.part_detail.thumbnail}
              size={80}
              align="center"
            />
          </Paper>
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '10px',
              alignItems: 'center'
            }}
          >
            <Text>{item.obj.location_detail.pathstring}</Text>
            <InvenTreeIcon icon="arrow_down" />
            <Suspense fallback={<Skeleton width="150px" />}>
              <Text>{data.pathstring}</Text>
            </Suspense>
          </div>
        </div>
      ),
      onConfirm: () => {
        api
          .post(apiUrl(ApiEndpoints.stock_transfer), {
            items: [
              {
                pk: item.obj.pk,
                quantity: value,
                batch: item.obj.batch,
                status: item.obj.status
              }
            ],
            location: item.obj.part_detail.default_location
          })
          .then((response) => {
            console.log(response);
            refresh();
            return response.data;
          })
          .catch((e) => {
            console.log(e);
            return null;
          });
      }
    });
  }

  const onChange = useCallback(
    (value: any) => {
      setValue(value);
      input.changeFn(input.idx, 'quantity', value);
    },
    [item]
  );

  return (
    <tr>
      <td>
        <div
          style={{
            display: 'flex',
            gap: '5px',
            alignItems: 'center'
          }}
        >
          <Thumbnail
            size={40}
            src={item.obj.part_detail.thumbnail}
            align="center"
          />
          <div>{item.obj.part_detail.name}</div>
        </div>
      </td>
      <td>{item.obj.location_detail.pathstring}</td>
      <td>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {item.obj.quantity}
          <StatusRenderer status={item.obj.status} type={ModelType.stockitem} />
        </div>
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
        <div style={{ display: 'flex', gap: '3px' }}>
          <ActionButton
            onClick={() => _moveToDefault()}
            icon={<InvenTreeIcon icon="default_location" />}
            tooltip="Move to default location"
            tooltipAlignment="top"
          />
          <ActionButton
            onClick={() => input.removeFn(input.idx)}
            icon={<InvenTreeIcon icon="square_x" />}
            tooltip="Remove from list"
            tooltipAlignment="top"
            color="red"
          />
        </div>
      </td>
    </tr>
  );
}

function stockTransferFields(item: any): ApiFormFieldSet {
  return useMemo(() => {
    const fields: ApiFormFieldSet = {
      items: {
        field_type: 'table',
        value: [
          {
            pk: item.pk,
            quantity: item.quantity,
            batch: item.batch,
            status: item.status,
            packaging: item.packaging,
            obj: item
          }
        ],
        modelRenderer: (val) => {
          console.log('Key:', val);
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
  }, [item]);
}

export function useTransferStockItem({
  itemId,
  refresh
}: {
  itemId: any;
  refresh: () => void;
}) {
  const fields = stockTransferFields(itemId);

  return useCreateApiFormModal({
    url: ApiEndpoints.stock_transfer,
    fields: fields,
    title: 'Transfer Stock'
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
