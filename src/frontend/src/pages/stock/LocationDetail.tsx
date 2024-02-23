import { t } from '@lingui/macro';
import { LoadingOverlay, Stack, Text } from '@mantine/core';
import { IconPackages, IconSitemap } from '@tabler/icons-react';
import { useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';

import { ActionButton } from '../../components/buttons/ActionButton';
import {
  ActionDropdown,
  BarcodeActionDropdown,
  DeleteItemAction,
  EditItemAction,
  LinkBarcodeAction,
  UnlinkBarcodeAction,
  ViewBarcodeAction
} from '../../components/items/ActionDropdown';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { StockLocationTree } from '../../components/nav/StockLocationTree';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { useTransferStockItem } from '../../forms/StockForms';
import { InvenTreeIcon } from '../../functions/icons';
import { useInstance } from '../../hooks/UseInstance';
import { PartListTable } from '../../tables/part/PartTable';
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

  const locationPanels: PanelType[] = useMemo(() => {
    return [
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
      },
      {
        name: 'default_parts',
        label: t`Default Parts`,
        icon: <IconPackages />,
        content: (
          <PartListTable
            props={{
              params: {
                default_location: location.pk ?? null
              }
            }}
          />
        )
      }
    ];
  }, [location, id]);

  const transferStockItems = useTransferStockItem({
    item: location.pk,
    model: 'location',
    refresh: () => refreshInstance()
  });

  const locationActions = useMemo(
    () => [
      <ActionButton
        icon={<InvenTreeIcon icon="stocktake" />}
        variant="outline"
        size="lg"
      />,
      <BarcodeActionDropdown
        actions={[
          ViewBarcodeAction({}),
          LinkBarcodeAction({
            disabled: location?.barcode_hash
          }),
          UnlinkBarcodeAction({
            disabled: !location?.barcode_hash
          }),
          {
            name: 'Scan in stock items',
            icon: <InvenTreeIcon icon="stock" />,
            tooltip: 'Scan items'
          },
          {
            name: 'Scan in container',
            icon: <InvenTreeIcon icon="unallocated_stock" />,
            tooltip: 'Scan container'
          }
        ]}
      />,
      <ActionDropdown
        key="reports"
        icon={<InvenTreeIcon icon="reports" />}
        actions={[
          {
            name: 'Print Label',
            icon: '',
            tooltip: 'Print label'
          },
          {
            name: 'Print Location Report',
            icon: '',
            tooltip: 'Print Report'
          }
        ]}
      />,
      <ActionDropdown
        key="operations"
        icon={<InvenTreeIcon icon="stock" />}
        actions={[
          {
            name: 'Count Stock',
            icon: <InvenTreeIcon icon="stocktake" />,
            tooltip: 'Count Stock'
          },
          {
            name: 'Transfer Stock',
            icon: <InvenTreeIcon icon="transfer" />,
            tooltip: 'Transfer Stock',
            onClick: () => location.pk && transferStockItems.open()
          }
        ]}
      />,
      <ActionDropdown
        key="location"
        icon={<InvenTreeIcon icon="actions" />}
        actions={[
          EditItemAction({
            onClick: () => {
              location.pk;
            }
          }),
          DeleteItemAction({})
        ]}
      />
    ],
    [location]
  );

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
          actions={locationActions}
        />
        <PanelGroup pageKey="stocklocation" panels={locationPanels} />
        {transferStockItems.modal}
      </Stack>
    </>
  );
}
