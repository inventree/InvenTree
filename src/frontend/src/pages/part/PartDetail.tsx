import { t } from '@lingui/macro';
import {
  Alert,
  Center,
  Grid,
  Loader,
  Skeleton,
  Stack,
  Text
} from '@mantine/core';
import {
  IconBookmarks,
  IconBuilding,
  IconCalendarStats,
  IconClipboardList,
  IconCurrencyDollar,
  IconInfoCircle,
  IconLayersLinked,
  IconList,
  IconListTree,
  IconLock,
  IconPackages,
  IconShoppingCart,
  IconStack2,
  IconTestPipe,
  IconTools,
  IconTruckDelivery,
  IconTruckReturn,
  IconVersions
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { type ReactNode, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import Select from 'react-select';

import AdminButton from '../../components/buttons/AdminButton';
import { PrintingActions } from '../../components/buttons/PrintingActions';
import {
  type DetailsField,
  DetailsTable
} from '../../components/details/Details';
import DetailsBadge from '../../components/details/DetailsBadge';
import { DetailsImage } from '../../components/details/DetailsImage';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import type { ApiFormFieldSet } from '../../components/forms/fields/ApiFormField';
import { Thumbnail } from '../../components/images/Thumbnail';
import {
  ActionDropdown,
  BarcodeActionDropdown,
  DeleteItemAction,
  DuplicateItemAction,
  EditItemAction,
  OptionsActionDropdown
} from '../../components/items/ActionDropdown';
import InstanceDetail from '../../components/nav/InstanceDetail';
import NavigationTree from '../../components/nav/NavigationTree';
import { PageDetail } from '../../components/nav/PageDetail';
import AttachmentPanel from '../../components/panels/AttachmentPanel';
import NotesPanel from '../../components/panels/NotesPanel';
import type { PanelType } from '../../components/panels/Panel';
import { PanelGroup } from '../../components/panels/PanelGroup';
import { RenderPart } from '../../components/render/Part';
import OrderPartsWizard from '../../components/wizards/OrderPartsWizard';
import { useApi } from '../../contexts/ApiContext';
import { formatPriceRange } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { usePartFields } from '../../forms/PartForms';
import {
  type StockOperationProps,
  useCountStockItem,
  useTransferStockItem
} from '../../forms/StockForms';
import { InvenTreeIcon } from '../../functions/icons';
import { getDetailUrl } from '../../functions/urls';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import { apiUrl } from '../../states/ApiState';
import {
  useGlobalSettingsState,
  useUserSettingsState
} from '../../states/SettingsState';
import { useUserState } from '../../states/UserState';
import { BomTable } from '../../tables/bom/BomTable';
import { UsedInTable } from '../../tables/bom/UsedInTable';
import { BuildOrderTable } from '../../tables/build/BuildOrderTable';
import { PartParameterTable } from '../../tables/part/PartParameterTable';
import PartPurchaseOrdersTable from '../../tables/part/PartPurchaseOrdersTable';
import PartTestTemplateTable from '../../tables/part/PartTestTemplateTable';
import { PartVariantTable } from '../../tables/part/PartVariantTable';
import { RelatedPartTable } from '../../tables/part/RelatedPartTable';
import { ReturnOrderTable } from '../../tables/sales/ReturnOrderTable';
import { SalesOrderTable } from '../../tables/sales/SalesOrderTable';
import { StockItemTable } from '../../tables/stock/StockItemTable';
import PartAllocationPanel from './PartAllocationPanel';
import PartPricingPanel from './PartPricingPanel';
import PartSchedulingDetail from './PartSchedulingDetail';
import PartStocktakeDetail from './PartStocktakeDetail';
import PartSupplierDetail from './PartSupplierDetail';

/**
 * Detail view for a single Part instance
 */
export default function PartDetail() {
  const { id } = useParams();

  const api = useApi();
  const navigate = useNavigate();
  const user = useUserState();

  const [treeOpen, setTreeOpen] = useState(false);

  const globalSettings = useGlobalSettingsState();
  const userSettings = useUserSettingsState();

  const { instance: serials } = useInstance({
    endpoint: ApiEndpoints.part_serial_numbers,
    pk: id,
    hasPrimaryKey: true,
    refetchOnMount: false,
    defaultValue: {}
  });

  const {
    instance: part,
    refreshInstance,
    instanceQuery,
    requestStatus
  } = useInstance({
    endpoint: ApiEndpoints.part_list,
    pk: id,
    params: {
      path_detail: true
    },
    refetchOnMount: true
  });

  const detailsPanel = useMemo(() => {
    if (instanceQuery.isFetching) {
      return <Skeleton />;
    }

    const data = { ...part };

    data.required =
      (data?.required_for_build_orders ?? 0) +
      (data?.required_for_sales_orders ?? 0);

    // Provide latest serial number info
    if (!!serials.latest) {
      data.latest_serial_number = serials.latest;
    }

    // Construct the details tables
    const tl: DetailsField[] = [
      {
        type: 'string',
        name: 'name',
        label: t`Name`,
        icon: 'part',
        copy: true
      },
      {
        type: 'string',
        name: 'IPN',
        label: t`IPN`,
        copy: true,
        hidden: !part.IPN
      },
      {
        type: 'string',
        name: 'description',
        label: t`Description`,
        copy: true
      },
      {
        type: 'link',
        name: 'variant_of',
        label: t`Variant of`,
        model: ModelType.part,
        hidden: !part.variant_of
      },
      {
        type: 'link',
        name: 'revision_of',
        label: t`Revision of`,
        model: ModelType.part,
        hidden: !part.revision_of
      },
      {
        type: 'string',
        name: 'revision',
        label: t`Revision`,
        hidden: !part.revision,
        copy: true
      },
      {
        type: 'link',
        name: 'category',
        label: t`Category`,
        model: ModelType.partcategory
      },
      {
        type: 'link',
        name: 'default_location',
        label: t`Default Location`,
        model: ModelType.stocklocation,
        hidden: !part.default_location
      },
      {
        type: 'link',
        name: 'category_default_location',
        label: t`Category Default Location`,
        model: ModelType.stocklocation,
        hidden: part.default_location || !part.category_default_location
      },
      {
        type: 'string',
        name: 'units',
        label: t`Units`,
        copy: true,
        hidden: !part.units
      },
      {
        type: 'string',
        name: 'keywords',
        label: t`Keywords`,
        copy: true,
        hidden: !part.keywords
      },
      {
        type: 'link',
        name: 'link',
        label: t`Link`,
        external: true,
        copy: true,
        hidden: !part.link
      }
    ];

    const tr: DetailsField[] = [
      {
        type: 'string',
        name: 'total_in_stock',
        unit: true,
        label: t`In Stock`
      },
      {
        type: 'string',
        name: 'unallocated_stock',
        unit: true,
        label: t`Available Stock`,
        hidden: part.total_in_stock == part.unallocated_stock
      },
      {
        type: 'string',
        name: 'variant_stock',
        unit: true,
        label: t`Variant Stock`,
        hidden: !part.variant_stock,
        icon: 'stock'
      },
      {
        type: 'string',
        name: 'minimum_stock',
        unit: true,
        label: t`Minimum Stock`,
        hidden: part.minimum_stock <= 0
      },
      {
        type: 'string',
        name: 'ordering',
        label: t`On order`,
        unit: true,
        hidden: !part.purchaseable || part.ordering <= 0
      },
      {
        type: 'string',
        name: 'required',
        label: t`Required for Orders`,
        hidden: part.required <= 0,
        icon: 'tick_off'
      },
      {
        type: 'progressbar',
        name: 'allocated_to_build_orders',
        total: part.required_for_build_orders,
        progress: part.allocated_to_build_orders,
        label: t`Allocated to Build Orders`,
        hidden:
          !part.component ||
          (part.required_for_build_orders <= 0 &&
            part.allocated_to_build_orders <= 0)
      },
      {
        type: 'progressbar',
        name: 'allocated_to_sales_orders',
        total: part.required_for_sales_orders,
        progress: part.allocated_to_sales_orders,
        label: t`Allocated to Sales Orders`,
        hidden:
          !part.salable ||
          (part.required_for_sales_orders <= 0 &&
            part.allocated_to_sales_orders <= 0)
      },
      {
        type: 'string',
        name: 'can_build',
        unit: true,
        label: t`Can Build`,
        hidden: true // TODO: Expose "can_build" to the API
      },
      {
        type: 'string',
        name: 'building',
        unit: true,
        label: t`In Production`,
        hidden: !part.assembly || !part.building
      }
    ];

    const bl: DetailsField[] = [
      {
        type: 'boolean',
        name: 'active',
        label: t`Active`
      },
      {
        type: 'boolean',
        name: 'locked',
        label: t`Locked`
      },
      {
        type: 'boolean',
        icon: 'template',
        name: 'is_template',
        label: t`Template Part`
      },
      {
        type: 'boolean',
        name: 'assembly',
        label: t`Assembled Part`
      },
      {
        type: 'boolean',
        name: 'component',
        label: t`Component Part`
      },
      {
        type: 'boolean',
        name: 'testable',
        label: t`Testable Part`,
        icon: 'test'
      },
      {
        type: 'boolean',
        name: 'trackable',
        label: t`Trackable Part`
      },
      {
        type: 'boolean',
        name: 'purchaseable',
        label: t`Purchaseable Part`
      },
      {
        type: 'boolean',
        name: 'salable',
        icon: 'saleable',
        label: t`Saleable Part`
      },
      {
        type: 'boolean',
        name: 'virtual',
        label: t`Virtual Part`
      },
      {
        type: 'boolean',
        name: 'starred',
        label: t`Subscribed`,
        icon: 'bell'
      }
    ];

    const br: DetailsField[] = [
      {
        type: 'string',
        name: 'creation_date',
        label: t`Creation Date`
      },
      {
        type: 'string',
        name: 'creation_user',
        label: t`Created By`,
        badge: 'user',
        icon: 'user',
        hidden: !part.creation_user
      },
      {
        type: 'string',
        name: 'responsible',
        label: t`Responsible`,
        badge: 'owner',
        hidden: !part.responsible
      },
      {
        type: 'link',
        name: 'default_supplier',
        label: t`Default Supplier`,
        model: ModelType.supplierpart,
        hidden: !part.default_supplier
      }
    ];

    // Add in price range data
    if (part.pricing_min || part.pricing_max) {
      br.push({
        type: 'string',
        name: 'pricing',
        label: t`Price Range`,
        value_formatter: () => {
          return formatPriceRange(part.pricing_min, part.pricing_max);
        }
      });
    }

    br.push({
      type: 'string',
      name: 'latest_serial_number',
      label: t`Latest Serial Number`,
      hidden: !part.trackable || !data.latest_serial_number,
      icon: 'serial'
    });

    return part ? (
      <ItemDetailsGrid>
        <Grid grow>
          <DetailsImage
            appRole={UserRoles.part}
            imageActions={{
              selectExisting: true,
              downloadImage: true,
              uploadFile: true,
              deleteFile: true
            }}
            src={part.image}
            apiPath={apiUrl(ApiEndpoints.part_list, part.pk)}
            refresh={refreshInstance}
            pk={part.pk}
          />
          <Grid.Col span={{ base: 12, sm: 8 }}>
            <DetailsTable fields={tl} item={data} />
          </Grid.Col>
        </Grid>
        <DetailsTable fields={tr} item={data} />
        <DetailsTable fields={bl} item={data} />
        <DetailsTable fields={br} item={data} />
      </ItemDetailsGrid>
    ) : (
      <Skeleton />
    );
  }, [
    globalSettings,
    part,
    id,
    serials,
    instanceQuery.isFetching,
    instanceQuery.data
  ]);

  // Part data panels (recalculate when part data changes)
  const partPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'details',
        label: t`Part Details`,
        icon: <IconInfoCircle />,
        content: detailsPanel
      },
      {
        name: 'parameters',
        label: t`Parameters`,
        icon: <IconList />,
        content: (
          <PartParameterTable
            partId={id ?? -1}
            partLocked={part?.locked == true}
          />
        )
      },
      {
        name: 'stock',
        label: t`Stock`,
        icon: <IconPackages />,
        content: part.pk ? (
          <StockItemTable
            tableName='part-stock'
            allowAdd
            params={{
              part: part.pk
            }}
          />
        ) : (
          <Center>
            <Loader />
          </Center>
        )
      },
      {
        name: 'variants',
        label: t`Variants`,
        icon: <IconVersions />,
        hidden: !part.is_template,
        content: <PartVariantTable part={part} />
      },
      {
        name: 'allocations',
        label: t`Allocations`,
        icon: <IconBookmarks />,
        hidden: !part.component && !part.salable,
        content: part.pk ? <PartAllocationPanel part={part} /> : <Skeleton />
      },
      {
        name: 'bom',
        label: t`Bill of Materials`,
        icon: <IconListTree />,
        hidden: !part.assembly,
        content: part?.pk ? (
          <BomTable partId={part.pk ?? -1} partLocked={part?.locked == true} />
        ) : (
          <Skeleton />
        )
      },
      {
        name: 'builds',
        label: t`Build Orders`,
        icon: <IconTools />,
        hidden: !part.assembly || !user.hasViewRole(UserRoles.build),
        content: part.pk ? <BuildOrderTable partId={part.pk} /> : <Skeleton />
      },
      {
        name: 'used_in',
        label: t`Used In`,
        icon: <IconStack2 />,
        hidden: !part.component,
        content: <UsedInTable partId={part.pk ?? -1} />
      },
      {
        name: 'pricing',
        label: t`Part Pricing`,
        icon: <IconCurrencyDollar />,
        content: part ? <PartPricingPanel part={part} /> : <Skeleton />
      },
      {
        name: 'suppliers',
        label: t`Suppliers`,
        icon: <IconBuilding />,
        hidden:
          !part.purchaseable || !user.hasViewRole(UserRoles.purchase_order),

        content: part.pk ? (
          <PartSupplierDetail partId={part.pk} />
        ) : (
          <Skeleton />
        )
      },
      {
        name: 'purchase_orders',
        label: t`Purchase Orders`,
        icon: <IconShoppingCart />,
        hidden:
          !part.purchaseable || !user.hasViewRole(UserRoles.purchase_order),
        content: part.pk ? (
          <PartPurchaseOrdersTable partId={part.pk} />
        ) : (
          <Skeleton />
        )
      },
      {
        name: 'sales_orders',
        label: t`Sales Orders`,
        icon: <IconTruckDelivery />,
        hidden: !part.salable || !user.hasViewRole(UserRoles.sales_order),
        content: part.pk ? <SalesOrderTable partId={part.pk} /> : <Skeleton />
      },
      {
        name: 'return_orders',
        label: t`Return Orders`,
        icon: <IconTruckReturn />,
        hidden:
          !part.salable ||
          !user.hasViewRole(UserRoles.return_order) ||
          !globalSettings.isSet('RETURNORDER_ENABLED'),
        content: part.pk ? <ReturnOrderTable partId={part.pk} /> : <Skeleton />
      },
      {
        name: 'stocktake',
        label: t`Stock History`,
        icon: <IconClipboardList />,
        content: part ? <PartStocktakeDetail partId={part.pk} /> : <Skeleton />,
        hidden:
          !user.hasViewRole(UserRoles.stocktake) ||
          !globalSettings.isSet('STOCKTAKE_ENABLE') ||
          !userSettings.isSet('DISPLAY_STOCKTAKE_TAB')
      },
      {
        name: 'scheduling',
        label: t`Scheduling`,
        icon: <IconCalendarStats />,
        content: part ? <PartSchedulingDetail part={part} /> : <Skeleton />,
        hidden: !userSettings.isSet('DISPLAY_SCHEDULE_TAB')
      },
      {
        name: 'test_templates',
        label: t`Test Templates`,
        icon: <IconTestPipe />,
        hidden: !part.testable,
        content: part?.pk ? (
          <PartTestTemplateTable partId={part?.pk} partLocked={part.locked} />
        ) : (
          <Skeleton />
        )
      },
      {
        name: 'related_parts',
        label: t`Related Parts`,
        icon: <IconLayersLinked />,
        content: <RelatedPartTable partId={part.pk ?? -1} />
      },
      AttachmentPanel({
        model_type: ModelType.part,
        model_id: part?.pk
      }),
      NotesPanel({
        model_type: ModelType.part,
        model_id: part?.pk
      })
    ];
  }, [id, part, user, globalSettings, userSettings, detailsPanel]);

  // Fetch information on part revision
  const partRevisionQuery = useQuery({
    refetchOnMount: true,
    queryKey: [
      'part_revisions',
      part.pk,
      part.revision_of,
      part.revision_count
    ],
    queryFn: async () => {
      if (!part.revision_of && !part.revision_count) {
        return [];
      }

      const revisions = [];

      // First, fetch information for the top-level part
      if (part.revision_of) {
        await api
          .get(apiUrl(ApiEndpoints.part_list, part.revision_of))
          .then((response) => {
            revisions.push(response.data);
          });
      } else {
        revisions.push(part);
      }

      const url = apiUrl(ApiEndpoints.part_list);

      await api
        .get(url, {
          params: {
            revision_of: part.revision_of || part.pk
          }
        })
        .then((response) => {
          switch (response.status) {
            case 200:
              response.data.forEach((r: any) => {
                revisions.push(r);
              });
              break;
            default:
              break;
          }
        })
        .catch(() => {});

      return revisions;
    }
  });

  const partRevisionOptions: any[] = useMemo(() => {
    if (partRevisionQuery.isFetching || !partRevisionQuery.data) {
      return [];
    }

    if (!part.revision_of && !part.revision_count) {
      return [];
    }

    const options: any[] = partRevisionQuery.data.map((revision: any) => {
      return {
        value: revision.pk,
        label: revision.full_name,
        part: revision
      };
    });

    // Add this part if not already available
    if (!options.find((o) => o.value == part.pk)) {
      options.push({
        value: part.pk,
        label: part.full_name,
        part: part
      });
    }

    return options.sort((a, b) => {
      return `${a.part.revision}`.localeCompare(b.part.revision);
    });
  }, [part, partRevisionQuery.isFetching, partRevisionQuery.data]);

  const breadcrumbs = useMemo(() => {
    return [
      { name: t`Parts`, url: '/part' },
      ...(part.category_path ?? []).map((c: any) => ({
        name: c.name,
        url: getDetailUrl(ModelType.partcategory, c.pk)
      }))
    ];
  }, [part]);

  const badges: ReactNode[] = useMemo(() => {
    if (instanceQuery.isFetching) {
      return [];
    }

    const required =
      part.required_for_build_orders + part.required_for_sales_orders;

    return [
      <DetailsBadge
        label={`${t`In Stock`}: ${part.total_in_stock}`}
        color={part.total_in_stock >= part.minimum_stock ? 'green' : 'orange'}
        visible={part.total_in_stock > 0}
        key='in_stock'
      />,
      <DetailsBadge
        label={`${t`Available`}: ${part.unallocated_stock}`}
        color='yellow'
        key='available_stock'
        visible={part.unallocated_stock != part.total_in_stock}
      />,
      <DetailsBadge
        label={t`No Stock`}
        color='orange'
        visible={part.total_in_stock == 0}
        key='no_stock'
      />,
      <DetailsBadge
        label={`${t`Required`}: ${required}`}
        color='grape'
        visible={required > 0}
        key='required'
      />,
      <DetailsBadge
        label={`${t`On Order`}: ${part.ordering}`}
        color='blue'
        visible={part.ordering > 0}
        key='on_order'
      />,
      <DetailsBadge
        label={`${t`In Production`}: ${part.building}`}
        color='blue'
        visible={part.building > 0}
        key='in_production'
      />,
      <DetailsBadge
        label={t`Inactive`}
        color='red'
        visible={!part.active}
        key='inactive'
      />
    ];
  }, [part, instanceQuery.isFetching]);

  const partFields = usePartFields({ create: false });

  const editPart = useEditApiFormModal({
    url: ApiEndpoints.part_list,
    pk: part.pk,
    title: t`Edit Part`,
    fields: partFields,
    onFormSuccess: refreshInstance
  });

  const createPartFields = usePartFields({ create: true });

  const duplicatePartFields: ApiFormFieldSet = useMemo(() => {
    return {
      ...createPartFields,
      duplicate: {
        children: {
          part: {
            value: part.pk,
            hidden: true
          },
          copy_image: {
            value: true
          },
          copy_bom: {
            value: globalSettings.isSet('PART_COPY_BOM')
          },
          copy_notes: {
            value: true
          },
          copy_parameters: {
            value: globalSettings.isSet('PART_COPY_PARAMETERS')
          }
        }
      }
    };
  }, [createPartFields, globalSettings, part]);

  const duplicatePart = useCreateApiFormModal({
    url: ApiEndpoints.part_list,
    title: t`Add Part`,
    fields: duplicatePartFields,
    initialData: {
      ...part,
      active: true,
      locked: false
    },
    follow: true,
    modelType: ModelType.part
  });

  const deletePart = useDeleteApiFormModal({
    url: ApiEndpoints.part_list,
    pk: part.pk,
    title: t`Delete Part`,
    onFormSuccess: () => {
      if (part.category) {
        navigate(getDetailUrl(ModelType.partcategory, part.category));
      } else {
        navigate('/part/');
      }
    },
    preFormContent: (
      <Alert color='red' title={t`Deleting this part cannot be reversed`}>
        <Stack gap='xs'>
          <Thumbnail src={part.thumbnail ?? part.image} text={part.full_name} />
        </Stack>
      </Alert>
    )
  });

  const stockActionProps: StockOperationProps = useMemo(() => {
    return {
      pk: part.pk,
      model: ModelType.part,
      refresh: refreshInstance,
      filters: {
        in_stock: true
      }
    };
  }, [part]);

  const countStockItems = useCountStockItem(stockActionProps);
  const transferStockItems = useTransferStockItem(stockActionProps);

  const orderPartsWizard = OrderPartsWizard({
    parts: [part]
  });

  const partActions = useMemo(() => {
    return [
      <AdminButton model={ModelType.part} id={part.pk} />,
      <BarcodeActionDropdown
        model={ModelType.part}
        pk={part.pk}
        hash={part?.barcode_hash}
        perm={user.hasChangeRole(UserRoles.part)}
        key='action_dropdown'
      />,
      <PrintingActions
        modelType={ModelType.part}
        items={[part.pk]}
        enableReports
        enableLabels
      />,
      <ActionDropdown
        tooltip={t`Stock Actions`}
        icon={<IconPackages />}
        actions={[
          {
            icon: (
              <InvenTreeIcon icon='stocktake' iconProps={{ color: 'blue' }} />
            ),
            name: t`Count Stock`,
            tooltip: t`Count part stock`,
            hidden: !user.hasChangeRole(UserRoles.stock),
            onClick: () => {
              part.pk && countStockItems.open();
            }
          },
          {
            icon: (
              <InvenTreeIcon icon='transfer' iconProps={{ color: 'blue' }} />
            ),
            name: t`Transfer Stock`,
            tooltip: t`Transfer part stock`,
            hidden: !user.hasChangeRole(UserRoles.stock),
            onClick: () => {
              part.pk && transferStockItems.open();
            }
          },
          {
            name: t`Order`,
            tooltip: t`Order Stock`,
            hidden:
              !user.hasAddRole(UserRoles.purchase_order) ||
              !part?.active ||
              !part?.purchaseable,
            icon: <IconShoppingCart color='blue' />,
            onClick: () => {
              orderPartsWizard.openWizard();
            }
          }
        ]}
      />,
      <OptionsActionDropdown
        tooltip={t`Part Actions`}
        actions={[
          DuplicateItemAction({
            hidden: !user.hasAddRole(UserRoles.part),
            onClick: () => duplicatePart.open()
          }),
          EditItemAction({
            hidden: !user.hasChangeRole(UserRoles.part),
            onClick: () => editPart.open()
          }),
          DeleteItemAction({
            hidden: !user.hasDeleteRole(UserRoles.part),
            disabled: part.active,
            onClick: () => deletePart.open()
          })
        ]}
      />
    ];
  }, [id, part, user]);

  const enableRevisionSelection: boolean = useMemo(() => {
    return (
      partRevisionOptions.length > 0 &&
      globalSettings.isSet('PART_ENABLE_REVISION')
    );
  }, [partRevisionOptions, globalSettings]);

  return (
    <>
      {duplicatePart.modal}
      {editPart.modal}
      {deletePart.modal}
      {orderPartsWizard.wizard}
      <InstanceDetail
        status={requestStatus}
        loading={instanceQuery.isFetching}
        requiredRole={UserRoles.part}
      >
        <Stack gap='xs'>
          {user.hasViewRole(UserRoles.part_category) && (
            <NavigationTree
              title={t`Part Categories`}
              modelType={ModelType.partcategory}
              endpoint={ApiEndpoints.category_tree}
              opened={treeOpen}
              onClose={() => {
                setTreeOpen(false);
              }}
              selectedId={part?.category}
            />
          )}
          <PageDetail
            title={`${t`Part`}: ${part.full_name}`}
            icon={
              part?.locked ? (
                <IconLock aria-label='part-lock-icon' />
              ) : undefined
            }
            subtitle={part.description}
            imageUrl={part.image}
            badges={badges}
            breadcrumbs={
              user.hasViewRole(UserRoles.part_category)
                ? breadcrumbs
                : undefined
            }
            lastCrumb={[
              {
                name: part.name,
                url: `/part/${part.pk}/`
              }
            ]}
            breadcrumbAction={() => {
              setTreeOpen(true);
            }}
            editAction={editPart.open}
            editEnabled={user.hasChangeRole(UserRoles.part)}
            actions={partActions}
            detail={
              enableRevisionSelection ? (
                <Stack gap='xs'>
                  <Text>{t`Select Part Revision`}</Text>
                  <Select
                    id='part-revision-select'
                    aria-label='part-revision-select'
                    options={partRevisionOptions}
                    value={{
                      value: part.pk,
                      label: part.full_name,
                      part: part
                    }}
                    isSearchable={false}
                    formatOptionLabel={(option: any) =>
                      RenderPart({
                        instance: option.part,
                        showSecondary: false
                      })
                    }
                    onChange={(value: any) => {
                      navigate(getDetailUrl(ModelType.part, value.value));
                    }}
                    styles={{
                      menuPortal: (base: any) => ({ ...base, zIndex: 9999 }),
                      menu: (base: any) => ({ ...base, zIndex: 9999 }),
                      menuList: (base: any) => ({ ...base, zIndex: 9999 })
                    }}
                  />
                </Stack>
              ) : null
            }
          />
          <PanelGroup
            pageKey='part'
            panels={partPanels}
            instance={part}
            model={ModelType.part}
            id={part.pk}
          />
          {transferStockItems.modal}
          {countStockItems.modal}
        </Stack>
      </InstanceDetail>
    </>
  );
}
