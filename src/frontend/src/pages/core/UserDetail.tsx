import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { t } from '@lingui/core/macro';
import { Badge, Group, Skeleton, Stack } from '@mantine/core';
import { IconInfoCircle } from '@tabler/icons-react';
import { type ReactNode, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import {
  type DetailsField,
  DetailsTable
} from '../../components/details/Details';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import {} from '../../components/items/ActionDropdown';
import InstanceDetail from '../../components/nav/InstanceDetail';
import { PageDetail } from '../../components/nav/PageDetail';
import type { PanelType } from '../../components/panels/Panel';
import { PanelGroup } from '../../components/panels/PanelGroup';
import {} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import { useGlobalSettingsState } from '../../states/SettingsStates';
import { useUserState } from '../../states/UserState';

/**
 * Detail page for a single user
 */
export default function UserDetail() {
  const { id } = useParams();

  const user = useUserState();
  const settings = useGlobalSettingsState();

  const { instance, instanceQuery } = useInstance({
    endpoint: ApiEndpoints.user_list,
    pk: id
  });

  const userGroups: any[] = useMemo(() => instance?.groups ?? [], [instance]);

  const detailsPanel = useMemo(() => {
    if (instanceQuery.isFetching) {
      return <Skeleton />;
    }

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
        hidden: !instance.first_name
      },
      {
        type: 'text',
        name: 'last_name',
        label: t`Last Name`,
        icon: 'info',
        copy: true,
        hidden: !instance.last_name
      },
      {
        type: 'text',
        name: 'email',
        label: t`Email`,
        copy: true,
        hidden: !instance.email
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
        label: t`Staff`,
        icon: 'info'
      },
      {
        type: 'boolean',
        name: 'is_superuser',
        label: t`Superuser`,
        icon: 'info'
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

    const br: DetailsField[] = [
      {
        type: 'text',
        name: 'displayname',
        label: t`Display Name`,
        icon: 'user',
        copy: true,
        hidden: !instance.displayname
      },
      {
        type: 'text',
        name: 'position',
        label: t`Position`,
        icon: 'info',
        hidden: !instance.position
      },

      {
        type: 'text',
        name: 'contact',
        label: t`Contact`,
        icon: 'email',
        copy: true,
        hidden: !instance.contact
      },
      {
        type: 'text',
        name: 'organisation',
        label: t`Organisation`,
        icon: 'info',
        copy: true,
        hidden: !instance.organisation
      },
      {
        type: 'text',
        name: 'status',
        label: t`Status`,
        icon: 'note',
        hidden: !instance.status
      },
      {
        type: 'text',
        name: 'location',
        label: t`Location`,
        icon: 'location',
        copy: true,
        hidden: !instance.location
      }
    ];

    const hasProfile =
      instance.displayname ||
      instance.position ||
      instance.contact ||
      instance.organisation ||
      instance.status ||
      instance.location;

    return (
      <ItemDetailsGrid>
        <DetailsTable fields={tl} item={instance} title={t`User Information`} />
        <DetailsTable fields={tr} item={instance} title={t`User Permissions`} />
        {hasProfile && settings.isSet('DISPLAY_PROFILE_INFO') && (
          <DetailsTable fields={br} item={instance} title={t`User Profile`} />
        )}
      </ItemDetailsGrid>
    );
  }, [instance, userGroups, instanceQuery]);

  const userPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'detail',
        label: t`User Details`,
        icon: <IconInfoCircle />,
        content: detailsPanel
      }
    ];
  }, [instance, id, user]);

  const userBadges: ReactNode[] = useMemo(() => {
    return instanceQuery.isLoading
      ? []
      : [
          instance.is_staff && (
            <Badge key='is_staff' color='blue'>{t`Staff`}</Badge>
          ),
          instance.is_superuser && (
            <Badge key='is_superuser' color='red'>{t`Superuser`}</Badge>
          ),
          !instance.is_staff && !instance.is_superuser && (
            <Badge key='is_normal' color='yellow'>{t`Basic user`}</Badge>
          ),
          instance.is_active ? (
            <Badge key='is_active' color='green'>{t`Active`}</Badge>
          ) : (
            <Badge key='is_inactive' color='red'>{t`Inactive`}</Badge>
          )
        ];
  }, [instance, instanceQuery]);

  return (
    <InstanceDetail query={instanceQuery}>
      <Stack gap='xs'>
        <PageDetail
          title={`${t`User`}: ${instance.username}`}
          imageUrl={instance?.image}
          badges={userBadges}
          breadcrumbs={[
            { name: t`System Overview`, url: '/core/' },

            { name: t`Users`, url: '/core/index/users/' }
          ]}
          lastCrumb={[
            { name: instance.username, url: `/core/user/${instance.pk}/` }
          ]}
        />
        <PanelGroup
          pageKey='user'
          panels={userPanels}
          model={ModelType.user}
          id={instance.pk}
          instance={instance}
          reloadInstance={instanceQuery.refetch}
        />
      </Stack>
    </InstanceDetail>
  );
}
