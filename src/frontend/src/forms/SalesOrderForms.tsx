import { IconAddressBook, IconUser, IconUsers } from '@tabler/icons-react';

import {
  ApiFormAdjustFilterType,
  ApiFormFieldSet
} from '../components/forms/fields/ApiFormField';

export function salesOrderFields(): ApiFormFieldSet {
  return {
    reference: {},
    description: {},
    customer: {
      filters: {
        is_customer: true
      }
    },
    customer_reference: {},
    project_code: {},
    order_currency: {},
    target_date: {},
    link: {},
    contact: {
      icon: <IconUser />,
      adjustFilters: (value: ApiFormAdjustFilterType) => {
        return {
          ...value.filters,
          company: value.data.customer
        };
      }
    },
    address: {
      icon: <IconAddressBook />,
      adjustFilters: (value: ApiFormAdjustFilterType) => {
        return {
          ...value.filters,
          company: value.data.customer
        };
      }
    },
    responsible: {
      icon: <IconUsers />
    }
  };
}
