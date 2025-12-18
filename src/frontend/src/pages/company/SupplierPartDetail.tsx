import { t } from '@lingui/core/macro';
import { Grid, Skeleton, Stack } from '@mantine/core';
import {
  IconCurrencyDollar,
  IconInfoCircle,
  IconPackages,
  IconShoppingCart
} from '@tabler/icons-react';
import { type ReactNode, useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import { formatDecimal } from '@lib/functions/Formatting';
import { getDetailUrl } from '@lib/functions/Navigation';
import AdminButton from '../../components/buttons/AdminButton';
import {
  type DetailsField,
  DetailsTable
} from '../../components/details/Details';
import DetailsBadge from '../../components/details/DetailsBadge';
import { DetailsImage } from '../../components/details/DetailsImage';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import {
  BarcodeActionDropdown,
  DeleteItemAction,
  DuplicateItemAction,
  EditItemAction,
  OptionsActionDropdown
} from '../../components/items/ActionDropdown';
import InstanceDetail from '../../components/nav/InstanceDetail';
import { PageDetail } from '../../components/nav/PageDetail';
import AttachmentPanel from '../../components/panels/AttachmentPanel';
import NotesPanel from '../../components/panels/NotesPanel';
import type { PanelType } from '../../components/panels/Panel';
import { PanelGroup } from '../../components/panels/PanelGroup';
import ParametersPanel from '../../components/panels/ParametersPanel';
import { useSupplierPartFields } from '../../forms/CompanyForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import { useUserState } from '../../states/UserState';
import { PurchaseOrderTable } from '../../tables/purchasing/PurchaseOrderTable';
import SupplierPriceBreakTable from '../../tables/purchasing/SupplierPriceBreakTable';
import { StockItemTable } from '../../tables/stock/StockItemTable';

export default function SupplierPartDetail() {
  const { id } = useParams();

  const user = useUserState();

  const navigate = useNavigate();

  const {
    instance: supplierPart,
    instanceQuery,
    refreshInstance
  } = useInstance({
    endpoint: ApiEndpoints.supplier_part_list,
    pk: id,
    hasPrimaryKey: true,
    params: {
      part_detail: true,
      supplier_detail: true,
      manufacturer_detail: true
    }
  });

  const detailsPanel = useMemo(() => {
    if (instanceQuery.isFetching) {
      return <Skeleton />;
    }

    const data = supplierPart ?? {};

    // Access nested data
    data.manufacturer = data.manufacturer_detail?.pk;
    data.MPN = data.manufacturer_part_detail?.MPN;
    data.manufacturer_part = data.manufacturer_part_detail?.pk;

    const tl: DetailsField[] = [
      {
        type: 'link',
        name: 'part',
        label: t`Internal Part`,
        model: ModelType.part,
        hidden: !supplierPart.part
      },
      {
        type: 'string',
        name: 'part_detail.IPN',
        label: t`IPN`,
        copy: true,
        hidden: !data.part_detail?.IPN,
        icon: 'serial'
      },
      {
        type: 'string',
        name: 'part_detail.description',
        label: t`Part Description`,
        copy: true,
        icon: 'info',
        hidden: !data.part_detail?.description
      },
      {
        type: 'link',
        external: true,
        name: 'link',
        label: t`External Link`,
        copy: true,
        hidden: !supplierPart.link
      },
      {
        type: 'string',
        name: 'note',
        label: t`Note`,
        copy: true,
        hidden: !supplierPart.note
      }
    ];

    const bl: DetailsField[] = [
      {
        type: 'link',
        name: 'supplier',
        label: t`Supplier`,
        model: ModelType.company,
        icon: 'suppliers',
        hidden: !supplierPart.supplier
      },
      {
        type: 'string',
        name: 'SKU',
        label: t`SKU`,
        copy: true,
        icon: 'reference'
      },
      {
        type: 'string',
        name: 'description',
        label: t`Description`,
        copy: true,
        hidden: !data.description
      },
      {
        type: 'link',
        name: 'manufacturer',
        label: t`Manufacturer`,
        model: ModelType.company,
        icon: 'manufacturers',
        hidden: !data.manufacturer
      },
      {
        type: 'link',
        name: 'manufacturer_part',
        model_field: 'MPN',
        label: t`Manufacturer Part`,
        model: ModelType.manufacturerpart,
        icon: 'reference',
        hidden: !data.manufacturer_part
      }
    ];

    const br: DetailsField[] = [
      {
        type: 'string',
        name: 'packaging',
        label: t`Packaging`,
        copy: true,
        hidden: !data.packaging
      },
      {
        type: 'string',
        name: 'pack_quantity',
        label: t`Pack Quantity`,
        copy: true,
        hidden: !data.pack_quantity,
        icon: 'packages'
      }
    ];

    const tr: DetailsField[] = [
      {
        type: 'number',
        name: 'in_stock',
        label: t`In Stock`,
        copy: true,
        icon: 'stock'
      },
      {
        type: 'number',
        name: 'on_order',
        label: t`On Order`,
        copy: true,
        icon: 'purchase_orders'
      },
      {
        type: 'number',
        name: 'available',
        label: t`Supplier Availability`,
        hidden: !data.availability_updated,
        copy: true,
        icon: 'packages'
      },
      {
        type: 'date',
        name: 'availability_updated',
        label: t`Availability Updated`,
        copy: true,
        hidden: !data.availability_updated,
        icon: 'calendar'
      }
    ];

    return (
      <ItemDetailsGrid>
        <Grid grow>
          <DetailsImage
            appRole={UserRoles.part}
            src={supplierPart?.part_detail?.image}
            apiPath={apiUrl(
              ApiEndpoints.part_list,
              supplierPart?.part_detail?.pk
            )}
            pk={supplierPart?.part_detail?.pk}
          />
          <Grid.Col span={8}>
            <DetailsTable title={t`Part Details`} fields={tl} item={data} />
          </Grid.Col>
        </Grid>
        <DetailsTable title={t`Supplier`} fields={bl} item={data} />
        <DetailsTable title={t`Packaging`} fields={br} item={data} />
        <DetailsTable title={t`Availability`} fields={tr} item={data} />
      </ItemDetailsGrid>
    );
  }, [supplierPart, instanceQuery.isFetching]);

  const panels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'details',
        label: t`Supplier Part Details`,
        icon: <IconInfoCircle />,
        content: detailsPanel
      },
      {
        name: 'stock',
        label: t`Received Stock`,
        icon: <IconPackages />,
        content: supplierPart?.pk ? (
          <StockItemTable
            tableName='supplier-stock'
            allowAdd={false}
            params={{ supplier_part: supplierPart.pk }}
          />
        ) : (
          <Skeleton />
        )
      },
      {
        name: 'purchaseorders',
        label: t`Purchase Orders`,
        icon: <IconShoppingCart />,
        content: supplierPart?.pk ? (
          <PurchaseOrderTable
            supplierId={supplierPart.supplier}
            supplierPartId={supplierPart.pk}
          />
        ) : (
          <Skeleton />
        )
      },
      {
        name: 'pricing',
        label: t`Supplier Pricing`,
        icon: <IconCurrencyDollar />,
        content: supplierPart?.pk ? (
          <SupplierPriceBreakTable supplierPart={supplierPart} />
        ) : (
          <Skeleton />
        )
      },
      ParametersPanel({
        model_type: ModelType.supplierpart,
        model_id: supplierPart?.pk
      }),
      AttachmentPanel({
        model_type: ModelType.supplierpart,
        model_id: supplierPart?.pk
      }),
      NotesPanel({
        model_type: ModelType.supplierpart,
        model_id: supplierPart?.pk
      })
    ];
  }, [supplierPart]);

  const supplierPartActions = useMemo(() => {
    return [
      <AdminButton model={ModelType.supplierpart} id={supplierPart.pk} />,
      <BarcodeActionDropdown
        model={ModelType.supplierpart}
        pk={supplierPart.pk}
        hash={supplierPart.barcode_hash}
        perm={user.hasChangeRole(UserRoles.purchase_order)}
      />,
      <OptionsActionDropdown
        tooltip={t`Supplier Part Actions`}
        actions={[
          DuplicateItemAction({
            hidden: !user.hasAddRole(UserRoles.purchase_order),
            onClick: () => duplicateSupplierPart.open()
          }),
          EditItemAction({
            hidden: !user.hasChangeRole(UserRoles.purchase_order),
            onClick: () => editSupplierPart.open()
          }),
          DeleteItemAction({
            hidden: !user.hasDeleteRole(UserRoles.purchase_order),
            onClick: () => deleteSupplierPart.open()
          })
        ]}
      />
    ];
  }, [user, supplierPart]);

  const supplierPartFields = useSupplierPartFields({});

  const editSupplierPart = useEditApiFormModal({
    url: ApiEndpoints.supplier_part_list,
    pk: supplierPart?.pk,
    title: t`Edit Supplier Part`,
    fields: supplierPartFields,
    onFormSuccess: refreshInstance
  });

  const deleteSupplierPart = useDeleteApiFormModal({
    url: ApiEndpoints.supplier_part_list,
    pk: supplierPart?.pk,
    title: t`Delete Supplier Part`,
    onFormSuccess: () => {
      navigate(getDetailUrl(ModelType.part, supplierPart.part));
    }
  });

  const duplicateSupplierPart = useCreateApiFormModal({
    url: ApiEndpoints.supplier_part_list,
    title: t`Add Supplier Part`,
    fields: supplierPartFields,
    initialData: {
      ...supplierPart
    },
    follow: true,
    modelType: ModelType.supplierpart
  });

  const breadcrumbs = useMemo(() => {
    return [
      {
        name: t`Purchasing`,
        url: '/purchasing/'
      },
      {
        name: supplierPart?.supplier_detail?.name ?? t`Supplier`,
        url: `/purchasing/supplier/${supplierPart?.supplier_detail?.pk ?? ''}`
      }
    ];
  }, [supplierPart]);

  const badges: ReactNode[] = useMemo(() => {
    return [
      <DetailsBadge
        label={t`Inactive`}
        color='red'
        visible={supplierPart.active == false}
      />,
      <DetailsBadge
        label={`${t`In Stock`}: ${formatDecimal(supplierPart.in_stock)}`}
        color={'green'}
        visible={
          supplierPart?.active &&
          supplierPart?.in_stock &&
          supplierPart?.in_stock > 0
        }
        key='in_stock'
      />,
      <DetailsBadge
        label={t`No Stock`}
        color={'red'}
        visible={supplierPart.active && supplierPart.in_stock == 0}
        key='no_stock'
      />,
      <DetailsBadge
        label={`${t`On Order`}: ${formatDecimal(supplierPart.on_order)}`}
        color='blue'
        visible={supplierPart.on_order > 0}
        key='on_order'
      />
    ];
  }, [supplierPart]);

  return (
    <>
      {deleteSupplierPart.modal}
      {duplicateSupplierPart.modal}
      {editSupplierPart.modal}
      <InstanceDetail
        query={instanceQuery}
        requiredRole={UserRoles.purchase_order}
      >
        <Stack gap='xs'>
          <PageDetail
            title={t`Supplier Part`}
            subtitle={`${supplierPart.SKU} - ${supplierPart?.part_detail?.name}`}
            breadcrumbs={breadcrumbs}
            lastCrumb={[
              {
                name: supplierPart.SKU,
                url: `/purchasing/supplier-part/${supplierPart.pk}/`
              }
            ]}
            badges={badges}
            actions={supplierPartActions}
            imageUrl={supplierPart?.part_detail?.thumbnail}
            editAction={editSupplierPart.open}
            editEnabled={user.hasChangePermission(ModelType.supplierpart)}
          />
          <PanelGroup
            pageKey='supplierpart'
            panels={panels}
            instance={supplierPart}
            reloadInstance={refreshInstance}
            model={ModelType.supplierpart}
            id={supplierPart.pk}
          />
        </Stack>
      </InstanceDetail>
    </>
  );
}
