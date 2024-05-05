import { t } from '@lingui/macro';
import {
  IconCalendar,
  IconLink,
  IconList,
  IconSitemap,
  IconTruckDelivery,
  IconUser,
  IconUsersGroup
} from '@tabler/icons-react';
import { useEffect, useMemo, useState } from 'react';

import { api } from '../App';
import { ApiFormFieldSet } from '../components/forms/fields/ApiFormField';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { apiUrl } from '../states/ApiState';

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

export function useBuildOrderOutputFields({
  build
}: {
  build: any;
}): ApiFormFieldSet {
  const trackable: boolean = useMemo(() => {
    return build.part_detail?.trackable ?? false;
  }, [build.part_detail]);

  const [location, setLocation] = useState<number | null>(null);

  useEffect(() => {
    setLocation(build.location || build.part_detail?.default_location || null);
  }, [build.location, build.part_detail]);

  const [quantity, setQuantity] = useState<number>(0);

  useEffect(() => {
    let build_quantity = build.quantity ?? 0;
    let build_complete = build.completed ?? 0;

    setQuantity(Math.max(0, build_quantity - build_complete));
  }, [build]);

  const [serialPlaceholder, setSerialPlaceholder] = useState<string>('');

  useEffect(() => {
    if (trackable) {
      api
        .get(apiUrl(ApiEndpoints.part_serial_numbers, build.part_detail.pk))
        .then((response: any) => {
          if (response.data?.next) {
            setSerialPlaceholder(
              t`Next serial number` + ' - ' + response.data.next
            );
          } else if (response.data?.latest) {
            setSerialPlaceholder(
              t`Latest serial number` + ' - ' + response.data.latest
            );
          } else {
            setSerialPlaceholder('');
          }
        })
        .catch(() => {
          setSerialPlaceholder('');
        });
    } else {
      setSerialPlaceholder('');
    }
  }, [build, trackable]);

  return useMemo(() => {
    return {
      quantity: {
        value: quantity,
        onValueChange: (value: any) => {
          setQuantity(value);
        }
      },
      serial_numbers: {
        hidden: !trackable,
        placeholder: serialPlaceholder
      },
      batch_code: {},
      location: {
        value: location,
        onValueChange: (value: any) => {
          setQuantity(value);
        }
      },
      auto_allocate: {
        hidden: !trackable
      }
    };
  }, [quantity, serialPlaceholder, trackable]);
}
