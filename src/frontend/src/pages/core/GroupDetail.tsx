import { ApiEndpoints } from '@lib/core';
import { ModelType } from '@lib/core';
import { useInstance } from '@lib/hooks';
import { t } from '@lingui/macro';
import { Grid, Skeleton, Stack } from '@mantine/core';
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

/**
 * Detail page for a single group
 */
export default function GroupDetail() {
  const { id } = useParams();

  const { instance, instanceQuery, requestStatus } = useInstance({
    endpoint: ApiEndpoints.group_list,
    pk: id
  });

  const detailsPanel = useMemo(() => {
    if (instanceQuery.isFetching) {
      return <Skeleton />;
    }

    const tl: DetailsField[] = [
      {
        type: 'text',
        name: 'name',
        label: t`Group Name`,
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
      </ItemDetailsGrid>
    );
  }, [instance, instanceQuery]);

  const groupPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'detail',
        label: t`Group Details`,
        icon: <IconInfoCircle />,
        content: detailsPanel
      }
    ];
  }, [instance, id]);

  const groupBadges: ReactNode[] = useMemo(() => {
    return instanceQuery.isLoading ? [] : ['group info'];
  }, [instance, instanceQuery]);

  return (
    <InstanceDetail status={requestStatus} loading={instanceQuery.isFetching}>
      <Stack gap='xs'>
        <PageDetail
          title={`${t`Group`}: ${instance.name}`}
          imageUrl={instance?.image}
          badges={groupBadges}
          breadcrumbs={[
            { name: t`System Overview`, url: '/core/' },
            { name: t`Groups`, url: '/core/index/groups/' }
          ]}
          lastCrumb={[
            { name: instance.name, url: `/core/group/${instance.pk}/` }
          ]}
        />
        <PanelGroup
          pageKey='group'
          panels={groupPanels}
          model={ModelType.group}
          id={instance.pk}
          instance={instance}
        />
      </Stack>
    </InstanceDetail>
  );
}
