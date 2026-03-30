import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import { getDetailUrl } from '@lib/functions/Navigation';
import type { StockOperationProps } from '@lib/types/Forms';
import { t } from '@lingui/core/macro';
import { Group, Skeleton, Stack, Text } from '@mantine/core';
import {
  IconInfoCircle,
  IconListDetails,
  IconPackages,
  IconSitemap,
  IconTable
} from '@tabler/icons-react';
import { useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../../App';
import { useBarcodeScanDialog } from '../../components/barcodes/BarcodeScanDialog';
import AdminButton from '../../components/buttons/AdminButton';
import { PrintingActions } from '../../components/buttons/PrintingActions';
import {
  type DetailsField,
  DetailsTable
} from '../../components/details/Details';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import {
  BarcodeActionDropdown,
  DeleteItemAction,
  EditItemAction,
  OptionsActionDropdown
} from '../../components/items/ActionDropdown';
import { ApiIcon } from '../../components/items/ApiIcon';
import InstanceDetail from '../../components/nav/InstanceDetail';
import NavigationTree from '../../components/nav/NavigationTree';
import { PageDetail } from '../../components/nav/PageDetail';
import type { PanelType } from '../../components/panels/Panel';
import { PanelGroup } from '../../components/panels/PanelGroup';
import ParametersPanel from '../../components/panels/ParametersPanel';
import SegmentedControlPanel from '../../components/panels/SegmentedControlPanel';
import LocateItemButton from '../../components/plugins/LocateItemButton';
import { stockLocationFields } from '../../forms/StockForms';
import { InvenTreeIcon } from '../../functions/icons';
import {
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import { useStockAdjustActions } from '../../hooks/UseStockAdjustActions';
import { useUserState } from '../../states/UserState';
import { PartListTable } from '../../tables/part/PartTable';
import { StockItemTable } from '../../tables/stock/StockItemTable';
import StockLocationParametricTable from '../../tables/stock/StockLocationParametricTable';
import { StockLocationTable } from '../../tables/stock/StockLocationTable';

export default function Stock() {
  const { id: _id } = useParams();

  const id = useMemo(
    () => (!Number.isNaN(Number.parseInt(_id || '')) ? _id : undefined),
    [_id]
  );

  const navigate = useNavigate();
  const user = useUserState();

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

    const left: DetailsField[] = [
      {
        type: 'text',
        name: 'name',
        label: t`Name`,
        copy: true,
        value_formatter: () => (
          <Group gap='xs'>
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

    const right: DetailsField[] = [
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

  const [sublocationView, setSublocationView] = useState<string>('table');

  const locationPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'details',
        label: t`Location Details`,
        icon: <IconInfoCircle />,
        content: detailsPanel
      },
      SegmentedControlPanel({
        name: 'sublocations',
        label: id ? t`Sublocations` : t`Stock Locations`,
        icon: <IconSitemap />,
        hidden: !user.hasViewPermission(ModelType.stocklocation),
        selection: sublocationView,
        onChange: setSublocationView,
        options: [
          {
            value: 'table',
            label: t`Table View`,
            icon: <IconTable />,
            content: <StockLocationTable parentId={id} />
          },
          {
            value: 'parametric',
            label: t`Parametric View`,
            icon: <IconListDetails />,
            content: (
              <StockLocationParametricTable
                queryParams={id ? { parent: id } : {}}
              />
            )
          }
        ]
      }),
      {
        name: 'stock-items',
        label: t`Stock Items`,
        icon: <IconPackages />,
        content: (
          <StockItemTable
            tableName='location-stock'
            allowAdd
            params={{
              location: id
            }}
          />
        )
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
      },
      ParametersPanel({
        model_type: ModelType.stocklocation,
        model_id: location.pk,
        hidden: !location.pk
      })
    ];
  }, [sublocationView, location, id]);

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
        value: 'false',
        display_name: t`Move items to parent location`
      },
      {
        value: 'true',
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
        required: true,
        description: t`Action for stock items in this location`,
        field_type: 'choice',
        choices: deleteOptions
      },
      delete_sub_locations: {
        label: t`Locations Action`,
        required: true,
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

  const stockOperationProps: StockOperationProps = useMemo(() => {
    return {
      pk: location.pk,
      model: 'location',
      refresh: refreshInstance,
      filters: {
        in_stock: true
      }
    };
  }, [location]);

  const stockAdjustActions = useStockAdjustActions({
    formProps: stockOperationProps,
    enabled: true,
    delete: false,
    merge: false,
    assign: false
  });

  const scanInStockItem = useBarcodeScanDialog({
    title: t`Scan Stock Item`,
    modelType: ModelType.stockitem,
    callback: async (barcode, response) => {
      const item = response.stockitem.instance;

      // Scan the stock item into the current location
      return api
        .post(apiUrl(ApiEndpoints.stock_transfer), {
          location: location.pk,
          items: [
            {
              pk: item.pk,
              quantity: item.quantity
            }
          ]
        })
        .then(() => {
          return {
            success: t`Scanned stock item into location`
          };
        })
        .catch((error) => {
          console.error('Error scanning stock item:', error);
          return {
            error: t`Error scanning stock item`
          };
        });
    }
  });

  const scanInStockLocation = useBarcodeScanDialog({
    title: t`Scan Stock Location`,
    modelType: ModelType.stocklocation,
    callback: async (barcode, response) => {
      const pk = response.stocklocation.pk;

      // Set the parent location
      return api
        .patch(apiUrl(ApiEndpoints.stock_location_list, pk), {
          parent: location.pk
        })
        .then(() => {
          return {
            success: t`Scanned stock location into location`
          };
        })
        .catch((error) => {
          console.error('Error scanning stock location:', error);
          return {
            error: t`Error scanning stock location`
          };
        });
    }
  });

  const locationActions = useMemo(
    () => [
      <AdminButton model={ModelType.stocklocation} id={location.pk} />,
      <LocateItemButton locationId={location.pk} />,
      location.pk ? (
        <BarcodeActionDropdown
          model={ModelType.stocklocation}
          pk={location.pk}
          hash={location?.barcode_hash}
          perm={user.hasChangeRole(UserRoles.stock_location)}
          actions={[
            {
              name: 'Scan in stock items',
              icon: <InvenTreeIcon icon='stock' />,
              tooltip: 'Scan item into this location',
              onClick: scanInStockItem.open
            },
            {
              name: 'Scan in container',
              icon: <InvenTreeIcon icon='unallocated_stock' />,
              tooltip: 'Scan container into this location',
              onClick: scanInStockLocation.open
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
      stockAdjustActions.dropdown,
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
    [location, id, user, stockAdjustActions.dropdown]
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
      {scanInStockItem.dialog}
      {scanInStockLocation.dialog}
      <InstanceDetail
        query={instanceQuery}
        requiredRole={UserRoles.stock_location}
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
            title={(location?.name ?? id) ? t`Stock Location` : t`Stock`}
            subtitle={location?.description}
            icon={location?.icon && <ApiIcon name={location?.icon} />}
            actions={locationActions}
            editAction={editLocation.open}
            editEnabled={
              !!location?.pk &&
              user.hasChangePermission(ModelType.stocklocation)
            }
            breadcrumbs={breadcrumbs}
            lastCrumb={[
              {
                name: location.name,
                url: `/stock/location/${location.pk}/`
              }
            ]}
            breadcrumbAction={() => {
              setTreeOpen(true);
            }}
          />
          <PanelGroup
            pageKey='stocklocation'
            panels={locationPanels}
            model={ModelType.stocklocation}
            reloadInstance={refreshInstance}
            id={location?.pk}
            instance={location}
          />
        </Stack>
        {stockAdjustActions.modals.map((modal) => modal.modal)}
      </InstanceDetail>
    </>
  );
}
