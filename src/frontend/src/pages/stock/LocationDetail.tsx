import { t } from '@lingui/macro';
import { LoadingOverlay, Stack, Text } from '@mantine/core';
import { IconPackages, IconSitemap } from '@tabler/icons-react';
import { useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';

import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { StockLocationTree } from '../../components/nav/StockLocationTree';
import { StockItemTable } from '../../components/tables/stock/StockItemTable';
import { StockLocationTable } from '../../components/tables/stock/StockLocationTable';
import { ApiPaths } from '../../enums/ApiEndpoints';
import { useInstance } from '../../hooks/UseInstance';

export function LocationPage({
  locationId
}: {
  locationId?: string | undefined;
}) {
  const [treeOpen, setTreeOpen] = useState(false);

  const {
    instance: location,
    refreshInstance,
    instanceQuery
  } = useInstance({
    endpoint: ApiPaths.stock_location_list,
    pk: locationId,
    hasPrimaryKey: true,
    params: {
      path_detail: true
    }
  });

  const locationPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'stock-items',
        label: t`Stock Items`,
        icon: <IconPackages />,
        content: (
          <StockItemTable
            params={{
              location: locationId
            }}
          />
        )
      },
      {
        name: 'sublocations',
        label: t`Stock Locations`,
        icon: <IconSitemap />,
        content: (
          <StockLocationTable
            params={{
              parent: locationId ?? 'null'
            }}
          />
        )
      }
    ];
  }, [locationId]);

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
        <StockLocationTree
          opened={treeOpen}
          onClose={() => setTreeOpen(false)}
          selectedLocation={location?.pk}
        />
        <PageDetail
          title={t`Stock Items`}
          detail={<Text>{location.name ?? 'Top level'}</Text>}
          breadcrumbs={breadcrumbs}
          breadcrumbAction={() => {
            setTreeOpen(true);
          }}
        />
        <PanelGroup pageKey="stocklocation" panels={locationPanels} />
      </Stack>
    </>
  );
}

/**
 * Detail page for a specific Stock Location instance
 * Uses the :id parameter in the URL to determine which location to display
 */
export default function LocationDetail({}: {}) {
  const { id } = useParams();

  return <LocationPage locationId={id} />;
}
