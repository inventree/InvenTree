import { t } from '@lingui/macro';
import {
  IconAt,
  IconCurrencyDollar,
  IconGlobe,
  IconPhone
} from '@tabler/icons-react';

import { ApiFormFieldSet } from '../components/forms/fields/ApiFormField';
import { openEditApiForm } from '../functions/forms';
import { ApiPaths } from '../states/ApiState';

/**
 * Field set for SupplierPart instance
 */
export function supplierPartFields(): ApiFormFieldSet {
  return {
    part: {
      filters: {
        purchaseable: true
      }
    },
    manufacturer_part: {
      filters: {
        part_detail: true,
        manufacturer_detail: true
      }
    },
    supplier: {},
    SKU: {},
    description: {},
    link: {},
    note: {},
    pack_quantity: {},
    packaging: {}
  };
}

/**
 * Field set for editing a company instance
 */
export function companyFields(): ApiFormFieldSet {
  return {
    name: {},
    description: {},
    website: {
      icon: <IconGlobe />
    },
    currency: {
      icon: <IconCurrencyDollar />
    },
    phone: {
      icon: <IconPhone />
    },
    email: {
      icon: <IconAt />
    },
    is_supplier: {},
    is_manufacturer: {},
    is_customer: {}
  };
}

/**
 * Edit a company instance
 */
export function editCompany({
  pk,
  callback
}: {
  pk: number;
  callback?: () => void;
}) {
  openEditApiForm({
    title: t`Edit Company`,
    url: ApiPaths.company_list,
    pk: pk,
    fields: companyFields(),
    successMessage: t`Company updated`,
    onFormSuccess: callback
  });
}
