import { IconAddressBook, IconUser, IconUsers } from '@tabler/icons-react';
import { useMemo } from 'react';

import {
  ApiFormAdjustFilterType,
  ApiFormFieldSet
} from '../components/forms/fields/ApiFormField';

export function useSalesOrderFields(): ApiFormFieldSet {
  return useMemo(() => {
    return {
      reference: {},
      description: {},
      customer: {
        filters: {
          is_customer: true,
          active: true
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
  }, []);
}

export function useReturnOrderFields(): ApiFormFieldSet {
  return useMemo(() => {
    return {
      reference: {},
      description: {},
      customer: {
        filters: {
          is_customer: true,
          active: true
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
  }, []);
}
