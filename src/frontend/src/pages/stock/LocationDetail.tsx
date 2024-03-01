import { t } from '@lingui/macro';
import { LoadingOverlay, Skeleton, Stack, Text } from '@mantine/core';
import { IconInfoCircle, IconPackages, IconSitemap } from '@tabler/icons-react';
import { useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';

import { DetailsField, DetailsTable } from '../../components/details/Details';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { StockLocationTree } from '../../components/nav/StockLocationTree';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { useInstance } from '../../hooks/UseInstance';
import { StockItemTable } from '../../tables/stock/StockItemTable';
import { StockLocationTable } from '../../tables/stock/StockLocationTable';

export default function Stock() {
  const { id: _id } = useParams();

  const id = useMemo(
    () => (!isNaN(parseInt(_id || '')) ? _id : undefined),
    [_id]
  );

  const [treeOpen, setTreeOpen] = useState(false);

  const {
    instance: location,
    refreshInstance,
    instanceQuery
  } = useInstance({
    endpoint: ApiEndpoints.stock_location_list,
    hasPrimaryKey: true,
    pk: id,
    params: {
      path_detail: true
    }
  });

  const detailsPanel = useMemo(() => {
    if (id && instanceQuery.isFetching) {
      return <Skeleton />;
    }

    let left: DetailsField[] = [
      {
        type: 'text',
        name: 'name',
        label: t`Name`,
        copy: true
      },
      {
        type: 'text',
        name: 'pathstring',
        label: t`Path`,
        icon: 'sitemap',
        copy: true,
        hidden: !id
      },
      {
        type: 'text',
        name: 'description',
        label: t`Description`,
        copy: true
      },
      {
        type: 'link',
        name: 'parent',
        model_field: 'name',
        icon: 'location',
        label: t`Parent Location`,
        model: ModelType.stocklocation,
        hidden: !location?.parent
      }
    ];

    let right: DetailsField[] = [
      {
        type: 'text',
        name: 'items',
        icon: 'stock',
        label: t`Stock Items`
      },
      {
        type: 'text',
        name: 'sublocations',
        icon: 'location',
        label: t`Sublocations`,
        hidden: !location?.sublocations
      },
      {
        type: 'boolean',
        name: 'structural',
        label: t`Structural`,
        icon: 'sitemap'
      },
      {
        type: 'boolean',
        name: 'external',
        label: t`External`
      }
    ];

    return (
      <ItemDetailsGrid>
        {id && location?.pk ? (
          <DetailsTable item={location} fields={left} />
        ) : (
          <Text>{t`Top level stock location`}</Text>
        )}
        {id && location?.pk && <DetailsTable item={location} fields={right} />}
      </ItemDetailsGrid>
    );
  }, [location, instanceQuery]);

  const locationPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'details',
        label: t`Location Details`,
        icon: <IconInfoCircle />,
        content: detailsPanel
      },
      {
        name: 'stock-items',
        label: t`Stock Items`,
        icon: <IconPackages />,
        content: (
          <StockItemTable
            params={{
              location: id
            }}
          />
        )
      },
      {
        name: 'sublocations',
        label: t`Stock Locations`,
        icon: <IconSitemap />,
        content: <StockLocationTable parentId={id} />
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
