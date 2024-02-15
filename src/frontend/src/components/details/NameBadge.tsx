import { Badge, Skeleton } from '@mantine/core';
import { useSuspenseQuery } from '@tanstack/react-query';
import { Suspense } from 'react';

import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { InvenTreeIcon } from '../../functions/icons';
import { apiUrl } from '../../states/ApiState';
import { useGlobalSettingsState } from '../../states/SettingsState';
import { BadgeType } from './DetailsField';

/**
 * Fetches user or group info from backend and formats into a badge.
 * Badge shows username, full name, or group name depending on server settings.
 * Badge appends icon to describe type of Owner
 */
export function NameBadge({
  pk,
  type
}: {
  pk: string | number;
  type: BadgeType;
}) {
  const { data } = useSuspenseQuery({
    queryKey: ['badge', type, pk],
    queryFn: async () => {
      let path: string = '';

      switch (type) {
        case 'owner':
          path = ApiEndpoints.owner_list;
          break;
        case 'user':
          path = ApiEndpoints.user_list;
          break;
        case 'group':
          path = ApiEndpoints.group_list;
          break;
      }

      const url = apiUrl(path, pk);

      return api
        .get(url)
        .then((response: any) => {
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

  const settings = useGlobalSettingsState();

  // Rendering a user's rame for the badge
  function _render_name() {
    if (type === 'user' && settings.isSet('DISPLAY_FULL_NAMES')) {
      if (data.first_name || data.last_name) {
        return `${data.first_name} ${data.last_name}`;
      } else {
        return data.username;
      }
    } else if (type === 'user') {
      return data.username;
    } else {
      return data.name;
    }
  }

  return (
    <Suspense fallback={<Skeleton width={200} height={20} radius="xl" />}>
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <Badge
          color="dark"
          variant="filled"
          style={{ display: 'flex', alignItems: 'center' }}
        >
          {data.name ?? _render_name()}
        </Badge>
        <InvenTreeIcon icon={type === 'user' ? type : data.label} />
      </div>
    </Suspense>
  );
}
