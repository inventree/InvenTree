import { t } from '@lingui/core/macro';
import { Badge, Group } from '@mantine/core';
import { useMemo } from 'react';

import type { DetailsField } from '../../components/details/Details';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import { useGlobalSettingsState } from '../../states/SettingsStates';

/**
 * Details panel for a single user.
 *
 * Used on the user detail page, and in the user preview drawer.
 */
export function UserDetailsPanel({ instance }: Readonly<{ instance: any }>) {
  const settings = useGlobalSettingsState();

  const userGroups: any[] = useMemo(() => instance?.groups ?? [], [instance]);

  const tl: DetailsField[] = [
    {
      type: 'text',
      name: 'username',
      label: t`Username`,
      icon: 'info',
      copy: true
    },
    {
      type: 'text',
      name: 'first_name',
      label: t`First Name`,
      icon: 'info',
      copy: true,
      hidden: !instance?.first_name
    },
    {
      type: 'text',
      name: 'last_name',
      label: t`Last Name`,
      icon: 'info',
      copy: true,
      hidden: !instance?.last_name
    },
    {
      type: 'text',
      name: 'email',
      label: t`Email`,
      copy: true,
      hidden: !instance?.email
    }
  ];

  const tr: DetailsField[] = [
    {
      type: 'boolean',
      name: 'is_active',
      label: t`Active`,
      icon: 'info'
    },
    {
      type: 'boolean',
      name: 'is_staff',
      label: t`Administrator`,
      icon: 'warning'
    },
    {
      type: 'boolean',
      name: 'is_superuser',
      label: t`Superuser`,
      icon: 'warning'
    },
    {
      type: 'text',
      name: 'groups',
      label: t`Groups`,
      icon: 'group',
      copy: false,
      hidden: !userGroups,
      value_formatter: () => {
        return (
          <Group gap='xs'>
            {userGroups?.map((group) => (
              <Badge key={group.pk}>{group.name}</Badge>
            ))}
          </Group>
        );
      }
    }
  ];

  // Profile information is provided as a nested object
  const profile = instance?.profile ?? {};

  const br: DetailsField[] = [
    {
      type: 'text',
      name: 'displayname',
      label: t`Display Name`,
      icon: 'user',
      copy: true,
      hidden: !profile.displayname
    },
    {
      type: 'text',
      name: 'position',
      label: t`Position`,
      icon: 'info',
      hidden: !profile.position
    },

    {
      type: 'text',
      name: 'contact',
      label: t`Contact`,
      icon: 'email',
      copy: true,
      hidden: !profile.contact
    },
    {
      type: 'text',
      name: 'organisation',
      label: t`Organisation`,
      icon: 'info',
      copy: true,
      hidden: !profile.organisation
    },
    {
      type: 'text',
      name: 'status',
      label: t`Status`,
      icon: 'note',
      hidden: !profile.status
    },
    {
      type: 'text',
      name: 'location',
      label: t`Location`,
      icon: 'location',
      copy: true,
      hidden: !profile.location
    }
  ];

  const hasProfile =
    profile.displayname ||
    profile.position ||
    profile.contact ||
    profile.organisation ||
    profile.status ||
    profile.location;

  return (
    <ItemDetailsGrid
      tables={[
        { fields: tl, item: instance, title: t`User Information` },
        { fields: tr, item: instance, title: t`User Permissions` },
        ...(hasProfile && settings.isSet('DISPLAY_PROFILE_INFO')
          ? [{ fields: br, item: profile, title: t`User Profile` }]
          : [])
      ]}
    />
  );
}
