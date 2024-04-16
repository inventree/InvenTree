import { IconAddressBook, IconUser, IconUsers } from '@tabler/icons-react';
import { useMemo } from 'react';

import {
  ApiFormAdjustFilterType,
  ApiFormFieldSet
} from '../components/forms/fields/ApiFormField';

export function useSalesOrderFields({
  create
}: {
  create: boolean;
}): ApiFormFieldSet {
  return useMemo(() => {
    return {
      reference: {},
      description: {},
      customer: {
        filters: {
          is_customer: true,
          active: create ? true : undefined
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
  }, [create]);
}

export function useReturnOrderFields({
  create
}: {
  create: boolean;
}): ApiFormFieldSet {
  return useMemo(() => {
    return {
      reference: {},
      description: {},
      customer: {
        filters: {
          is_customer: true,
          active: create ? true : undefined
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
  }, [create]);
}
