import { t } from '@lingui/macro';
import { Alert, Grid, Skeleton, Stack, Table } from '@mantine/core';
import {
  IconBookmarks,
  IconBuilding,
  IconBuildingFactory2,
  IconCalendarStats,
  IconClipboardList,
  IconCurrencyDollar,
  IconDots,
  IconInfoCircle,
  IconLayersLinked,
  IconList,
  IconListTree,
  IconNotes,
  IconPackages,
  IconPaperclip,
  IconShoppingCart,
  IconStack2,
  IconTestPipe,
  IconTools,
  IconTruckDelivery,
  IconVersions
} from '@tabler/icons-react';
import { useSuspenseQuery } from '@tanstack/react-query';
import { ReactNode, useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { api } from '../../App';
import AdminButton from '../../components/buttons/AdminButton';
import { DetailsField, DetailsTable } from '../../components/details/Details';
import DetailsBadge from '../../components/details/DetailsBadge';
import { DetailsImage } from '../../components/details/DetailsImage';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import { PartIcons } from '../../components/details/PartIcons';
import NotesEditor from '../../components/editors/NotesEditor';
import { Thumbnail } from '../../components/images/Thumbnail';
import {
  ActionDropdown,
  BarcodeActionDropdown,
  DeleteItemAction,
  DuplicateItemAction,
  EditItemAction,
  LinkBarcodeAction,
  UnlinkBarcodeAction,
  ViewBarcodeAction
} from '../../components/items/ActionDropdown';
import { PlaceholderPanel } from '../../components/items/Placeholder';
import InstanceDetail from '../../components/nav/InstanceDetail';
import NavigationTree from '../../components/nav/NavigationTree';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { formatPriceRange } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { usePartFields } from '../../forms/PartForms';
import {
  StockOperationProps,
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
import { useUserState } from '../../states/UserState';
import { BomTable } from '../../tables/bom/BomTable';
import { UsedInTable } from '../../tables/bom/UsedInTable';
import { BuildOrderTable } from '../../tables/build/BuildOrderTable';
import { AttachmentTable } from '../../tables/general/AttachmentTable';
import { PartParameterTable } from '../../tables/part/PartParameterTable';
import PartTestTemplateTable from '../../tables/part/PartTestTemplateTable';
import { PartVariantTable } from '../../tables/part/PartVariantTable';
import { RelatedPartTable } from '../../tables/part/RelatedPartTable';
import { ManufacturerPartTable } from '../../tables/purchasing/ManufacturerPartTable';
import { SupplierPartTable } from '../../tables/purchasing/SupplierPartTable';
import { SalesOrderTable } from '../../tables/sales/SalesOrderTable';
import { StockItemTable } from '../../tables/stock/StockItemTable';
import PartPricingPanel from './PartPricingPanel';

/**
 * Detail view for a single Part instance
 */
export default function PartDetail() {
  const { id } = useParams();

  const navigate = useNavigate();
  const user = useUserState();

  const [treeOpen, setTreeOpen] = useState(false);

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

    // Construct the details tables
    let tl: DetailsField[] = [
      {
        type: 'string',
        name: 'name',
        label: t`Name`,
        icon: 'part',
        copy: true
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
        name: 'IPN',
        label: t`IPN`,
        copy: true,
        hidden: !part.IPN
      },
      {
        type: 'string',
        name: 'revision',
        label: t`Revision`,
        copy: true,
        hidden: !part.revision
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

    let tr: DetailsField[] = [
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
        hidden: part.ordering <= 0
      },
      {
        type: 'progressbar',
        name: 'allocated_to_build_orders',
        total: part.required_for_build_orders,
        progress: part.allocated_to_build_orders,
        label: t`Allocated to Build Orders`,
        hidden: !part.component || part.required_for_build_orders <= 0
      },
      {
        type: 'progressbar',
        name: 'allocated_to_sales_orders',
        total: part.required_for_sales_orders,
        progress: part.allocated_to_sales_orders,
        label: t`Allocated to Sales Orders`,
        hidden: !part.salable || part.required_for_sales_orders <= 0
      },
      {
        type: 'string',
        name: 'can_build',
        unit: true,
        label: t`Can Build`,
        hidden: !part.assembly
      },
      {
        type: 'string',
        name: 'building',
        unit: true,
        label: t`Building`,
        hidden: !part.assembly
      }
    ];

    let bl: DetailsField[] = [
      {
        type: 'boolean',
        name: 'active',
        label: t`Active`
      },
      {
        type: 'boolean',
        name: 'template',
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
        name: 'saleable',
        label: t`Saleable Part`
      },
      {
        type: 'boolean',
        name: 'virtual',
        label: t`Virtual Part`
      }
    ];

    let br: DetailsField[] = [
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
    id &&
      br.push({
        type: 'string',
        name: 'pricing',
        label: t`Price Range`,
        value_formatter: () => {
          const { data } = useSuspenseQuery({
            queryKey: ['pricing', id],
            queryFn: async () => {
              const url = apiUrl(ApiEndpoints.part_pricing_get, null, {
                id: id
              });

              return api
                .get(url)
                .then((response) => {
                  switch (response.status) {
                    case 200:
                      return response.data;
                    default:
                      return null;
                  }
                })
                .catch(() => {
                  return null;
                });
            }
          });

          return (
            data &&
            `${formatPriceRange(data.overall_min, data.overall_max)}${
              part.units && ' / ' + part.units
            }`
          );
        }
      });

    // Add in stocktake information
    if (id && part.last_stocktake) {
      br.push({
        type: 'string',
        name: 'stocktake',
        label: t`Last Stocktake`,
        unit: true,
        value_formatter: () => {
          const { data } = useSuspenseQuery({
            queryKey: ['stocktake', id],
            queryFn: async () => {
              const url = apiUrl(ApiEndpoints.part_stocktake_list);

              return api
                .get(url, { params: { part: id, ordering: 'date' } })
                .then((response) => {
                  switch (response.status) {
                    case 200:
                      return response.data[response.data.length - 1];
                    default:
                      return null;
                  }
                })
                .catch(() => {
                  return null;
                });
            }
          });

          if (data.quantity) {
            return `${data.quantity} (${data.date})`;
          } else {
            return '-';
          }
        }
      });

      br.push({
        type: 'string',
        name: 'stocktake_user',
        label: t`Stocktake By`,
        badge: 'user',
        icon: 'user',
        value_formatter: () => {
          const { data } = useSuspenseQuery({
            queryKey: ['stocktake', id],
            queryFn: async () => {
              const url = apiUrl(ApiEndpoints.part_stocktake_list);

              return api
                .get(url, { params: { part: id, ordering: 'date' } })
                .then((response) => {
                  switch (response.status) {
                    case 200:
                      return response.data[response.data.length - 1];
                    default:
                      return null;
                  }
                })
                .catch(() => {
                  return null;
                });
            }
          });
          return data?.user;
        }
      });
    }

    return (
      <ItemDetailsGrid>
        <Grid>
          <Grid.Col span={4}>
            <DetailsImage
              appRole={UserRoles.part}
              imageActions={{
                selectExisting: true,
                uploadFile: true,
                deleteFile: true
              }}
              src={part.image}
              apiPath={apiUrl(ApiEndpoints.part_list, part.pk)}
              refresh={refreshInstance}
              pk={part.pk}
            />
          </Grid.Col>
          <Grid.Col span={8}>
            <Stack gap="xs">
              <Table>
                <Table.Tbody>
                  <Table.Tr>
                    <PartIcons part={part} />
                  </Table.Tr>
                </Table.Tbody>
              </Table>
              <DetailsTable fields={tl} item={part} />
            </Stack>
          </Grid.Col>
        </Grid>
        <DetailsTable fields={tr} item={part} />
        <DetailsTable fields={bl} item={part} />
        <DetailsTable fields={br} item={part} />
      </ItemDetailsGrid>
    );
  }, [part, instanceQuery]);

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
        content: <PartParameterTable partId={id ?? -1} />
      },
      {
        name: 'stock',
        label: t`Stock`,
        icon: <IconPackages />,
        content: part.pk && (
          <StockItemTable
            tableName="part-stock"
            allowAdd
            params={{
              part: part.pk
            }}
          />
        )
      },
      {
        name: 'variants',
        label: t`Variants`,
        icon: <IconVersions />,
        hidden: !part.is_template,
        content: <PartVariantTable partId={String(id)} />
      },
      {
        name: 'allocations',
        label: t`Allocations`,
        icon: <IconBookmarks />,
        hidden: !part.component && !part.salable,
        content: <PlaceholderPanel />
      },
      {
        name: 'bom',
        label: t`Bill of Materials`,
        icon: <IconListTree />,
        hidden: !part.assembly,
        content: <BomTable partId={part.pk ?? -1} />
      },
      {
        name: 'builds',
        label: t`Build Orders`,
        icon: <IconTools />,
        hidden: !part.assembly,
        content: part?.pk ? <BuildOrderTable partId={part.pk} /> : <Skeleton />
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
        name: 'manufacturers',
        label: t`Manufacturers`,
        icon: <IconBuildingFactory2 />,
        hidden: !part.purchaseable,
        content: part.pk && (
          <ManufacturerPartTable
            params={{
              part: part.pk
            }}
          />
        )
      },
      {
        name: 'suppliers',
        label: t`Suppliers`,
        icon: <IconBuilding />,
        hidden: !part.purchaseable,
        content: part.pk && (
          <SupplierPartTable
            params={{
              part: part.pk
            }}
          />
        )
      },
      {
        name: 'purchase_orders',
        label: t`Purchase Orders`,
        icon: <IconShoppingCart />,
        hidden: !part.purchaseable,
        content: <PlaceholderPanel />
      },
      {
        name: 'sales_orders',
        label: t`Sales Orders`,
        icon: <IconTruckDelivery />,
        hidden: !part.salable,
        content: part.pk ? <SalesOrderTable partId={part.pk} /> : <Skeleton />
      },
      {
        name: 'scheduling',
        label: t`Scheduling`,
        icon: <IconCalendarStats />,
        content: <PlaceholderPanel />
      },
      {
        name: 'stocktake',
        label: t`Stocktake`,
        icon: <IconClipboardList />,
        content: <PlaceholderPanel />
      },
      {
        name: 'test_templates',
        label: t`Test Templates`,
        icon: <IconTestPipe />,
        hidden: !part.trackable,
        content: part?.pk ? (
          <PartTestTemplateTable partId={part?.pk} />
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
      {
        name: 'attachments',
        label: t`Attachments`,
        icon: <IconPaperclip />,
        content: (
          <AttachmentTable model_type={ModelType.part} model_id={part?.pk} />
        )
      },
      {
        name: 'notes',
        label: t`Notes`,
        icon: <IconNotes />,
        content: (
          <NotesEditor
            modelType={ModelType.part}
            modelId={part.pk}
            editable={user.hasChangeRole(UserRoles.part)}
          />
        )
      }
    ];
  }, [id, part, user]);

  const breadcrumbs = useMemo(
    () => [
      { name: t`Parts`, url: '/part' },
      ...(part.category_path ?? []).map((c: any) => ({
        name: c.name,
        url: getDetailUrl(ModelType.partcategory, c.pk)
      }))
    ],
    [part]
  );

  const badges: ReactNode[] = useMemo(() => {
    if (instanceQuery.isLoading || instanceQuery.isFetching) {
      return [];
    }

    return [
      <DetailsBadge
        label={t`In Stock` + `: ${part.total_in_stock}`}
        color={part.in_stock >= part.minimum_stock ? 'green' : 'orange'}
        visible={part.in_stock > 0}
        key="in_stock"
      />,
      <DetailsBadge
        label={t`Available` + `: ${part.unallocated_stock}`}
        color="yellow"
        key="available_stock"
        visible={part.unallocated_stock != part.total_in_stock}
      />,
      <DetailsBadge
        label={t`No Stock`}
        color="red"
        visible={part.in_stock == 0}
        key="no_stock"
      />,
      <DetailsBadge
        label={t`On Order` + `: ${part.ordering}`}
        color="blue"
        visible={part.on_order > 0}
        key="on_order"
      />,
      <DetailsBadge
        label={t`In Production` + `: ${part.building}`}
        color="blue"
        visible={part.building > 0}
        key="in_production"
      />,
      <DetailsBadge
        label={t`Inactive`}
        color="red"
        visible={part.active == false}
        key="inactive"
      />
    ];
  }, [part, instanceQuery]);

  const partFields = usePartFields({ create: false });

  const editPart = useEditApiFormModal({
    url: ApiEndpoints.part_list,
    pk: part.pk,
    title: t`Edit Part`,
    fields: partFields,
    onFormSuccess: refreshInstance
  });

  const duplicatePart = useCreateApiFormModal({
    url: ApiEndpoints.part_list,
    title: t`Add Part`,
    fields: partFields,
    initialData: {
      ...part
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
      <Alert color="red" title={t`Deleting this part cannot be reversed`}>
        <Stack gap="xs">
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

  const partActions = useMemo(() => {
    return [
      <AdminButton model={ModelType.part} pk={part.pk} />,
      <BarcodeActionDropdown
        actions={[
          ViewBarcodeAction({}),
          LinkBarcodeAction({
            hidden: part?.barcode_hash || !user.hasChangeRole(UserRoles.part)
          }),
          UnlinkBarcodeAction({
            hidden: !part?.barcode_hash || !user.hasChangeRole(UserRoles.part)
          })
        ]}
        key="action_dropdown"
      />,
      <ActionDropdown
        tooltip={t`Stock Actions`}
        icon={<IconPackages />}
        actions={[
          {
            icon: (
              <InvenTreeIcon icon="stocktake" iconProps={{ color: 'blue' }} />
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
              <InvenTreeIcon icon="transfer" iconProps={{ color: 'blue' }} />
            ),
            name: t`Transfer Stock`,
            tooltip: t`Transfer part stock`,
            hidden: !user.hasChangeRole(UserRoles.stock),
            onClick: () => {
              part.pk && transferStockItems.open();
            }
          }
        ]}
      />,
      <ActionDropdown
        tooltip={t`Part Actions`}
        icon={<IconDots />}
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

  return (
    <>
      {duplicatePart.modal}
      {editPart.modal}
      {deletePart.modal}
      <InstanceDetail status={requestStatus} loading={instanceQuery.isFetching}>
        <Stack gap="xs">
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
          <PageDetail
            title={t`Part` + ': ' + part.full_name}
            subtitle={part.description}
            imageUrl={part.image}
            badges={badges}
            breadcrumbs={breadcrumbs}
            breadcrumbAction={() => {
              setTreeOpen(true);
            }}
            actions={partActions}
          />
          <PanelGroup pageKey="part" panels={partPanels} />
          {transferStockItems.modal}
          {countStockItems.modal}
        </Stack>
      </InstanceDetail>
    </>
  );
}
