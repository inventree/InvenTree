import {
  IconCalendar,
  IconLink,
  IconList,
  IconSitemap,
  IconTruckDelivery,
  IconUser,
  IconUsersGroup
} from '@tabler/icons-react';
import { useMemo, useState } from 'react';

import { ApiFormFieldSet } from '../components/forms/fields/ApiFormField';

/**
 * Field set for BuildOrder forms
 */
export function useBuildOrderFields({
  create
}: {
  create: boolean;
}): ApiFormFieldSet {
  const [destination, setDestination] = useState<number | null | undefined>(
    null
  );

  return useMemo(() => {
    return {
      reference: {},
      part: {
        filters: {
          assembly: true,
          virtual: false
        },
        onValueChange(value: any, record?: any) {
          // Adjust the destination location for the build order
          if (record) {
            setDestination(
              record.default_location || record.category_default_location
            );
          }
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
        },
        value: destination
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
  }, [create, destination]);
}
