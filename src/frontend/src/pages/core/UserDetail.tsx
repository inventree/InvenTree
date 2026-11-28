import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import type { PanelType } from '@lib/types/Panel';
import { t } from '@lingui/core/macro';
import { Badge, Skeleton, Stack } from '@mantine/core';
import { IconInfoCircle } from '@tabler/icons-react';
import { type ReactNode, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import {} from '../../components/items/ActionDropdown';
import InstanceDetail from '../../components/nav/InstanceDetail';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup } from '../../components/panels/PanelGroup';
import {} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import { useUserState } from '../../states/UserState';
import { UserDetailsPanel } from './UserDetailsPanel';

/**
 * Detail page for a single user
 */
export default function UserDetail() {
  const { id } = useParams();

  const user = useUserState();

  const { instance, instanceQuery } = useInstance({
    endpoint: ApiEndpoints.user_list,
    pk: id
  });

  const detailsPanel = useMemo(() => {
    if (instanceQuery.isFetching) {
      return <Skeleton />;
    }

    return <UserDetailsPanel instance={instance} />;
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
            <Badge key='is_staff' color='orange'>{t`Administrator`}</Badge>
          ),
          instance.is_superuser && (
            <Badge key='is_superuser' color='red'>{t`Superuser`}</Badge>
          ),
          !instance.is_staff && !instance.is_superuser && (
            <Badge key='is_normal' color='yellow'>{t`Normal user`}</Badge>
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
          model={ModelType.user}
          id={instance.pk}
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
