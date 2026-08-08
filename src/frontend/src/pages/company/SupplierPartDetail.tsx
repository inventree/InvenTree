import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { formatDecimal } from '@lib/functions/Formatting';
import { getDetailUrl } from '@lib/functions/Navigation';
import type { PanelType } from '@lib/types/Panel';
import { t } from '@lingui/core/macro';
import { Skeleton, Stack } from '@mantine/core';
import {
  IconCurrencyDollar,
  IconInfoCircle,
  IconPackages,
  IconShoppingCart
} from '@tabler/icons-react';
import { type ReactNode, useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import AdminButton from '../../components/buttons/AdminButton';
import DetailsBadge from '../../components/details/DetailsBadge';
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
import { SupplierPartDetailsPanel } from './SupplierPartDetailsPanel';

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
      manufacturer_detail: true,
      tags: true
    }
  });

  const panels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'details',
        label: t`Supplier Part Details`,
        icon: <IconInfoCircle />,
        content: (
          <SupplierPartDetailsPanel
            instance={supplierPart}
            allowImageEdit
            refreshInstance={refreshInstance}
          />
        )
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
        model_id: supplierPart?.pk,
        has_note: !!supplierPart?.notes
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
    queryParams: new URLSearchParams({ tags: 'true' }),
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

  const duplicateSupplierPartFields = useSupplierPartFields({
    duplicateSupplierPartId: supplierPart?.pk
  });

  const duplicateSupplierPart = useCreateApiFormModal({
    url: ApiEndpoints.supplier_part_list,
    title: t`Add Supplier Part`,
    fields: duplicateSupplierPartFields,
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
