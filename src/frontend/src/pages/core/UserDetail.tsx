import { t } from '@lingui/macro';
import { Badge, Grid, Skeleton, Stack } from '@mantine/core';
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
import { ApiEndpoints } from '../../lib/enums/ApiEndpoints';
import { ModelType } from '../../lib/enums/ModelType';
import { useGlobalSettingsState } from '../../states/SettingsState';
import { useUserState } from '../../states/UserState';

/**
 * Detail page for a single user
 */
export default function UserDetail() {
  const { id } = useParams();

  const user = useUserState();
  const settings = useGlobalSettingsState();

  const { instance, instanceQuery, requestStatus } = useInstance({
    endpoint: ApiEndpoints.user_list,
    pk: id
  });

  const detailsPanel = useMemo(() => {
    if (instanceQuery.isFetching) {
      return <Skeleton />;
    }

    const tl: DetailsField[] = [
      {
        type: 'text',
        name: 'email',
        label: t`Email`,
        copy: true
      },
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
        copy: true
      },
      {
        type: 'text',
        name: 'last_name',
        label: t`Last Name`,
        icon: 'info',
        copy: true
      }
    ];

    const tr: DetailsField[] = [
      {
        type: 'text',
        name: 'displayname',
        label: t`Display Name`,
        icon: 'user',
        copy: true
      },
      {
        type: 'text',
        name: 'position',
        label: t`Position`,
        icon: 'info'
      },
      {
        type: 'boolean',
        name: 'active',
        label: t`Active`,
        icon: 'info'
      },
      {
        type: 'text',
        name: 'contact',
        label: t`Contact`,
        icon: 'email',
        copy: true
      },
      {
        type: 'text',
        name: 'organisation',
        label: t`Organisation`,
        icon: 'info',
        copy: true
      },
      {
        type: 'text',
        name: 'status',
        label: t`Status`,
        icon: 'note'
      },
      {
        type: 'text',
        name: 'location',
        label: t`Location`,
        icon: 'location',
        copy: true
      }
    ];

    return (
      <ItemDetailsGrid>
        <Grid grow>
          <Grid.Col span={{ base: 12, sm: 8 }}>
            <DetailsTable fields={tl} item={instance} />
          </Grid.Col>
        </Grid>
        {settings.isSet('DISPLAY_PROFILE_INFO') && (
          <DetailsTable fields={tr} item={instance} />
        )}
      </ItemDetailsGrid>
    );
  }, [instance, instanceQuery]);

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
    <InstanceDetail status={requestStatus} loading={instanceQuery.isFetching}>
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
        />
      </Stack>
    </InstanceDetail>
  );
}
