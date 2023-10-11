import { t } from '@lingui/macro';
import { LoadingOverlay, Stack, Text } from '@mantine/core';
import { IconPackages, IconSitemap } from '@tabler/icons-react';
import { useMemo } from 'react';
import { useParams } from 'react-router-dom';

import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { StockItemTable } from '../../components/tables/stock/StockItemTable';
import { StockLocationTable } from '../../components/tables/stock/StockLocationTable';
import { useInstance } from '../../hooks/UseInstance';
import { ApiPaths } from '../../states/ApiState';

export default function Stock() {
  const { id } = useParams();

  const {
    instance: location,
    refreshInstance,
    instanceQuery
  } = useInstance({
    endpoint: ApiPaths.stock_location_list,
    pk: id,
    params: {
      path_detail: true
    }
  });

  const locationPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'stock-items',
        label: t`Stock Items`,
        icon: <IconPackages size="18" />,
        content: (
          <StockItemTable
            params={{
              location: location.pk ?? null
            }}
          />
        )
      },
      {
        name: 'sublocations',
        label: t`Sublocations`,
        icon: <IconSitemap size="18" />,
        content: (
          <StockLocationTable
            params={{
              parent: location.pk ?? null
            }}
          />
        )
      }
    ];
  }, [location, id]);

  const breadcrumbs = useMemo(
    () => [
      { name: t`Stock`, url: '/stock' },
      ...(location.path ?? []).map((l: any) => ({
        name: l.name,
        url: `/stock/location/${l.pk}`
      }))
    ],
    [location]
  );

  return (
    <>
      <Stack>
        <LoadingOverlay visible={instanceQuery.isFetching} />
        <PageDetail
          title={t`Stock Items`}
          detail={<Text>{location.name ?? 'Top level'}</Text>}
          breadcrumbs={breadcrumbs}
        />
        <PanelGroup panels={locationPanels} />
      </Stack>
    </>
  );
}
