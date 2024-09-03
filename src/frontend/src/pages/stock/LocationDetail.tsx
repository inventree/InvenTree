import { t } from '@lingui/macro';
import { Group, Skeleton, Stack, Text } from '@mantine/core';
import { IconInfoCircle, IconPackages, IconSitemap } from '@tabler/icons-react';
import { useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { ActionButton } from '../../components/buttons/ActionButton';
import AdminButton from '../../components/buttons/AdminButton';
import { PrintingActions } from '../../components/buttons/PrintingActions';
import { DetailsField, DetailsTable } from '../../components/details/Details';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import {
  ActionDropdown,
  BarcodeActionDropdown,
  DeleteItemAction,
  EditItemAction,
  OptionsActionDropdown
} from '../../components/items/ActionDropdown';
import { ApiIcon } from '../../components/items/ApiIcon';
import InstanceDetail from '../../components/nav/InstanceDetail';
import NavigationTree from '../../components/nav/NavigationTree';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import {
  StockOperationProps,
  stockLocationFields,
  useCountStockItem,
  useTransferStockItem
} from '../../forms/StockForms';
import { InvenTreeIcon } from '../../functions/icons';
import { notYetImplemented } from '../../functions/notifications';
import { getDetailUrl } from '../../functions/urls';
import {
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import { useUserState } from '../../states/UserState';
import { PartListTable } from '../../tables/part/PartTable';
import { StockItemTable } from '../../tables/stock/StockItemTable';
import { StockLocationTable } from '../../tables/stock/StockLocationTable';

export default function Stock() {
  const { id: _id } = useParams();

  const id = useMemo(
    () => (!isNaN(parseInt(_id || '')) ? _id : undefined),
    [_id]
  );

  const navigate = useNavigate();
  const user = useUserState();

  const [treeOpen, setTreeOpen] = useState(false);

  const {
    instance: location,
    refreshInstance,
    instanceQuery,
    requestStatus
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
        copy: true,
        value_formatter: () => (
          <Group gap="xs">
            {location.icon && <ApiIcon name={location.icon} />}
            {location.name}
          </Group>
        )
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
        label: t`Stock Items`,
        value_formatter: () => location?.items || '0'
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
      },
      {
        type: 'string',
        // TODO: render location type icon here (ref: #7237)
        name: 'location_type_detail.name',
        label: t`Location Type`,
        hidden: !location?.location_type,
        icon: 'packages'
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
            tableName="location-stock"
            allowAdd
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
        hidden: !location.pk,
        content: (
          <PartListTable
            props={{
              params: {
                default_location: location.pk
              }
            }}
          />
        )
      }
    ];
  }, [location, id]);

  const editLocation = useEditApiFormModal({
    url: ApiEndpoints.stock_location_list,
    pk: id,
    title: t`Edit Stock Location`,
    fields: stockLocationFields(),
    onFormSuccess: refreshInstance
  });

  const deleteOptions = useMemo(() => {
    return [
      {
        value: 0,
        display_name: `Move items to parent location`
      },
      {
        value: 1,
        display_name: t`Delete items`
      }
    ];
  }, []);

  const deleteLocation = useDeleteApiFormModal({
    url: ApiEndpoints.stock_location_list,
    pk: id,
    title: t`Delete Stock Location`,
    fields: {
      delete_stock_items: {
        label: t`Items Action`,
        description: t`Action for stock items in this location`,
        field_type: 'choice',
        choices: deleteOptions
      },
      delete_sub_location: {
        label: t`Child Locations Action`,
        description: t`Action for child locations in this location`,
        field_type: 'choice',
        choices: deleteOptions
      }
    },
    onFormSuccess: () => {
      if (location.parent) {
        navigate(getDetailUrl(ModelType.stocklocation, location.parent));
      } else {
        navigate('/stock/');
      }
    }
  });

  const stockItemActionProps: StockOperationProps = useMemo(() => {
    return {
      pk: location.pk,
      model: 'location',
      refresh: refreshInstance,
      filters: {
        in_stock: true
      }
    };
  }, [location]);

  const transferStockItems = useTransferStockItem(stockItemActionProps);
  const countStockItems = useCountStockItem(stockItemActionProps);

  const locationActions = useMemo(
    () => [
      <AdminButton model={ModelType.stocklocation} pk={location.pk} />,
      <ActionButton
        icon={<InvenTreeIcon icon="stocktake" />}
        onClick={notYetImplemented}
        variant="outline"
        size="lg"
      />,
      location.pk ? (
        <BarcodeActionDropdown
          model={ModelType.stocklocation}
          pk={location.pk}
          actions={[
            {
              name: 'Scan in stock items',
              icon: <InvenTreeIcon icon="stock" />,
              tooltip: 'Scan items',
              onClick: notYetImplemented
            },
            {
              name: 'Scan in container',
              icon: <InvenTreeIcon icon="unallocated_stock" />,
              tooltip: 'Scan container',
              onClick: notYetImplemented
            }
          ]}
        />
      ) : null,
      <PrintingActions
        modelType={ModelType.stocklocation}
        items={[location.pk ?? 0]}
        hidden={!location?.pk}
        enableLabels
        enableReports
      />,
      <ActionDropdown
        tooltip={t`Stock Actions`}
        icon={<InvenTreeIcon icon="stock" />}
        actions={[
          {
            name: 'Count Stock',
            icon: (
              <InvenTreeIcon icon="stocktake" iconProps={{ color: 'blue' }} />
            ),
            tooltip: 'Count Stock',
            onClick: () => countStockItems.open()
          },
          {
            name: 'Transfer Stock',
            icon: (
              <InvenTreeIcon icon="transfer" iconProps={{ color: 'blue' }} />
            ),
            tooltip: 'Transfer Stock',
            onClick: () => transferStockItems.open()
          }
        ]}
      />,
      <OptionsActionDropdown
        tooltip={t`Location Actions`}
        actions={[
          EditItemAction({
            hidden: !id || !user.hasChangeRole(UserRoles.stock_location),
            tooltip: t`Edit Stock Location`,
            onClick: () => editLocation.open()
          }),
          DeleteItemAction({
            hidden: !id || !user.hasDeleteRole(UserRoles.stock_location),
            tooltip: t`Delete Stock Location`,
            onClick: () => deleteLocation.open()
          })
        ]}
      />
    ],
    [location, id, user]
  );

  const breadcrumbs = useMemo(
    () => [
      { name: t`Stock`, url: '/stock' },
      ...(location.path ?? []).map((l: any) => ({
        name: l.name,
        url: getDetailUrl(ModelType.stocklocation, l.pk),
        icon: l.icon ? <ApiIcon name={l.icon} /> : undefined
      }))
    ],
    [location]
  );

  return (
    <>
      {editLocation.modal}
      {deleteLocation.modal}
      <InstanceDetail
        status={requestStatus}
        loading={id ? instanceQuery.isFetching : false}
      >
        <Stack>
          <NavigationTree
            title={t`Stock Locations`}
            modelType={ModelType.stocklocation}
            endpoint={ApiEndpoints.stock_location_tree}
            opened={treeOpen}
            onClose={() => setTreeOpen(false)}
            selectedId={location?.pk}
          />
          <PageDetail
            title={t`Stock Items`}
            subtitle={location?.name}
            icon={location?.icon && <ApiIcon name={location?.icon} />}
            actions={locationActions}
            editAction={editLocation.open}
            editEnabled={user.hasChangePermission(ModelType.stocklocation)}
            breadcrumbs={breadcrumbs}
            breadcrumbAction={() => {
              setTreeOpen(true);
            }}
          />
          <PanelGroup pageKey="stocklocation" panels={locationPanels} />
          {transferStockItems.modal}
          {countStockItems.modal}
        </Stack>
      </InstanceDetail>
    </>
  );
}
