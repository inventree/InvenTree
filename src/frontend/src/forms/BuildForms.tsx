import {
  IconCalendar,
  IconLink,
  IconList,
  IconSitemap,
  IconTruckDelivery,
  IconUser,
  IconUsersGroup
} from '@tabler/icons-react';

import { ApiFormFieldSet } from '../components/forms/fields/ApiFormField';

/**
 * Field set for BuildOrder forms
 */
export function buildOrderFields(): ApiFormFieldSet {
  return {
    reference: {},
    part: {
      filters: {
        assembly: true,
        virtual: false
      }
    },
    title: {},
    quantity: {},
    project_code: {
      icon: <IconList />
    },
    priority: {},
    parent: {
      icon: <IconSitemap />,
      filters: {
        part_detail: true
      }
    },
    sales_order: {
      icon: <IconTruckDelivery />
    },
    batch: {},
    target_date: {
      icon: <IconCalendar />
    },
    take_from: {},
    destination: {
      filters: {
        structural: false
      }
    },
    link: {
      icon: <IconLink />
    },
    issued_by: {
      icon: <IconUser />
    },
    responsible: {
      icon: <IconUsersGroup />,
      filters: {
        is_active: true
      }
    }
  };
}
