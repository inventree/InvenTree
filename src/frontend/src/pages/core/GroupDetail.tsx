import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { t } from '@lingui/core/macro';
import { Paper, Skeleton, Stack } from '@mantine/core';
import { IconInfoCircle } from '@tabler/icons-react';
import { useMemo } from 'react';
import { useParams } from 'react-router-dom';
import {
  type DetailsField,
  DetailsTable
} from '../../components/details/Details';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import {} from '../../components/items/ActionDropdown';
import { RoleTable, type RuleSet } from '../../components/items/RoleTable';
import { StylishText } from '../../components/items/StylishText';
import InstanceDetail from '../../components/nav/InstanceDetail';
import { PageDetail } from '../../components/nav/PageDetail';
import type { PanelType } from '../../components/panels/Panel';
import { PanelGroup } from '../../components/panels/PanelGroup';
import {} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';

/**
 * Detail page for a single group
 */
export default function GroupDetail() {
  const { id } = useParams();

  const { instance, instanceQuery } = useInstance({
    endpoint: ApiEndpoints.group_list,
    pk: id
  });

  const detailsPanel = useMemo(() => {
    if (instanceQuery.isFetching) {
      return <Skeleton />;
    }

    const roles: RuleSet[] = instance?.roles ?? [];

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
        <DetailsTable fields={tl} item={instance} title={t`Group Details`} />
        <Paper p='xs' withBorder>
          <Stack gap='xs'>
            <StylishText size='lg'>{t`Group Roles`}</StylishText>
            <RoleTable roles={roles} />
          </Stack>
        </Paper>
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

  return (
    <InstanceDetail query={instanceQuery}>
      <Stack gap='xs'>
        <PageDetail
          title={`${t`Group`}: ${instance.name}`}
          imageUrl={instance?.image}
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
          reloadInstance={instanceQuery.refetch}
        />
      </Stack>
    </InstanceDetail>
  );
}
