import { t } from '@lingui/macro';
import { useMemo, useState } from 'react';

import { ApiFormFieldSet } from '../components/forms/fields/ApiFormField';
import { ApiPaths } from '../enums/ApiEndpoints';
import { useCreateApiFormModal, useEditApiFormModal } from '../hooks/UseForm';

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
    url: ApiPaths.stock_item_list,
    fields: fields,
    title: t`Create Stock Item`
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
    url: ApiPaths.stock_item_list,
    pk: item_id,
    fields: fields,
    title: t`Edit Stock Item`,
    successMessage: t`Stock item updated`,
    onFormSuccess: callback
  });
}
