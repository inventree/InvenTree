import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { getOverviewUrl } from '@lib/functions/Navigation';
import type { PanelType } from '@lib/types/Panel';
import { t } from '@lingui/core/macro';
import { Stack } from '@mantine/core';
import { IconInfoCircle } from '@tabler/icons-react';
import { useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { DetailsTable } from '../../components/details/Details';
import { ApiIcon } from '../../components/items/ApiIcon';
import InstanceDetail from '../../components/nav/InstanceDetail';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup } from '../../components/panels/PanelGroup';
import { useInstance } from '../../hooks/UseInstance';
import { useUserState } from '../../states/UserState';

export default function LocationTypeDetail() {
  const { id } = useParams();
  const isStaff = useUserState((state) => state.isStaff());
  const {
    instance: locationType,
    instanceQuery,
    refreshInstance
  } = useInstance({
    endpoint: ApiEndpoints.stock_location_type_list,
    pk: id
  });

  const panels = useMemo<PanelType[]>(
    () => [
      {
        name: 'details',
        label: t`Details`,
        icon: <IconInfoCircle />,
        content: (
          <DetailsTable
            item={locationType}
            fields={[
              { type: 'text', name: 'name', label: t`Name`, copy: true },
              { type: 'text', name: 'description', label: t`Description` },
              {
                type: 'number',
                name: 'location_count',
                label: t`Stock Locations`,
                icon: 'location'
              }
            ]}
          />
        )
      }
    ],
    [locationType]
  );

  return (
    <InstanceDetail
      query={instanceQuery}
      requiredPermission={ModelType.stocklocationtype}
    >
      <Stack gap='xs'>
        <PageDetail
          model={ModelType.stocklocationtype}
          id={locationType.pk}
          title={locationType.name}
          subtitle={t`Stock Location Type`}
          icon={locationType.icon && <ApiIcon name={locationType.icon} />}
          breadcrumbs={[
            { name: t`Stock`, url: getOverviewUrl(ModelType.stocklocation) },
            ...(isStaff
              ? [
                  {
                    name: t`Location Types`,
                    url: '/settings/admin/location-types'
                  }
                ]
              : [])
          ]}
        />
        <PanelGroup
          pageKey='stocklocationtype'
          panels={panels}
          model={ModelType.stocklocationtype}
          id={locationType.pk}
          instance={locationType}
          reloadInstance={refreshInstance}
        />
      </Stack>
    </InstanceDetail>
  );
}
