import { t } from '@lingui/macro';
import { Grid, Skeleton, Stack } from '@mantine/core';
import {
  IconCurrencyDollar,
  IconInfoCircle,
  IconNotes,
  IconPackages,
  IconShoppingCart
} from '@tabler/icons-react';
import { ReactNode, useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import AdminButton from '../../components/buttons/AdminButton';
import { DetailsField, DetailsTable } from '../../components/details/Details';
import DetailsBadge from '../../components/details/DetailsBadge';
import { DetailsImage } from '../../components/details/DetailsImage';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import NotesEditor from '../../components/editors/NotesEditor';
import {
  BarcodeActionDropdown,
  DeleteItemAction,
  DuplicateItemAction,
  EditItemAction,
  OptionsActionDropdown
} from '../../components/items/ActionDropdown';
import InstanceDetail from '../../components/nav/InstanceDetail';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { useSupplierPartFields } from '../../forms/CompanyForms';
import { getDetailUrl } from '../../functions/urls';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import { apiUrl } from '../../states/ApiState';
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
    refreshInstance,
    requestStatus
  } = useInstance({
    endpoint: ApiEndpoints.supplier_part_list,
    pk: id,
    hasPrimaryKey: true,
    params: {
      part_detail: true,
      supplier_detail: true
    }
  });

  const detailsPanel = useMemo(() => {
    if (instanceQuery.isFetching) {
      return <Skeleton />;
    }

    let data = supplierPart ?? {};

    // Access nested data
    data.manufacturer = data.manufacturer_detail?.pk;
    data.MPN = data.manufacturer_part_detail?.MPN;
    data.manufacturer_part = data.manufacturer_part_detail?.pk;

    let tl: DetailsField[] = [
      {
        type: 'link',
        name: 'part',
        label: t`Internal Part`,
        model: ModelType.part,
        hidden: !supplierPart.part
      },
      {
        type: 'string',
        name: 'description',
        label: t`Description`,
        copy: true
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

    let tr: DetailsField[] = [
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
        label: t`Manufacturer Part Number`,
        model: ModelType.manufacturerpart,
        copy: true,
        icon: 'reference',
        hidden: !data.manufacturer_part
      }
    ];

    let bl: DetailsField[] = [
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

    let br: DetailsField[] = [
      {
        type: 'string',
        name: 'available',
        label: t`Supplier Availability`,
        copy: true,
        icon: 'packages'
      },
      {
        type: 'string',
        name: 'availability_updated',
        label: t`Availability Updated`,
        copy: true,
        hidden: !data.availability_updated,
        icon: 'calendar'
      }
    ];

    return (
      <ItemDetailsGrid>
        <Grid>
          <Grid.Col span={4}>
            <DetailsImage
              appRole={UserRoles.part}
              src={supplierPart?.part_detail?.image}
              apiPath={apiUrl(
                ApiEndpoints.part_list,
                supplierPart?.part_detail?.pk
              )}
              pk={supplierPart?.part_detail?.pk}
            />
          </Grid.Col>
          <Grid.Col span={8}>
            <DetailsTable title={t`Supplier Part`} fields={tl} item={data} />
          </Grid.Col>
        </Grid>
        <DetailsTable title={t`Supplier`} fields={tr} item={data} />
        <DetailsTable title={t`Packaging`} fields={bl} item={data} />
        <DetailsTable title={t`Availability`} fields={br} item={data} />
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
            tableName="supplier-stock"
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
          <PurchaseOrderTable supplierPartId={supplierPart.pk} />
        ) : (
          <Skeleton />
        )
      },
      {
        name: 'pricing',
        label: t`Supplier Pricing`,
        icon: <IconCurrencyDollar />,
        content: supplierPart?.pk ? (
          <SupplierPriceBreakTable supplierPartId={supplierPart.pk} />
        ) : (
          <Skeleton />
        )
      },
      {
        name: 'notes',
        label: t`Notes`,
        icon: <IconNotes />,
        content: (
          <NotesEditor
            modelType={ModelType.supplierpart}
            modelId={supplierPart.pk}
            editable={user.hasChangeRole(UserRoles.purchase_order)}
          />
        )
      }
    ];
  }, [supplierPart]);

  const supplierPartActions = useMemo(() => {
    return [
      <AdminButton model={ModelType.supplierpart} pk={supplierPart.pk} />,
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

  const supplierPartFields = useSupplierPartFields();

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
        color="red"
        visible={supplierPart.active == false}
      />
    ];
  }, [supplierPart]);

  return (
    <>
      {deleteSupplierPart.modal}
      {duplicateSupplierPart.modal}
      {editSupplierPart.modal}
      <InstanceDetail status={requestStatus} loading={instanceQuery.isFetching}>
        <Stack gap="xs">
          <PageDetail
            title={t`Supplier Part`}
            subtitle={`${supplierPart.SKU} - ${supplierPart?.part_detail?.name}`}
            breadcrumbs={breadcrumbs}
            badges={badges}
            actions={supplierPartActions}
            imageUrl={supplierPart?.part_detail?.thumbnail}
            editAction={editSupplierPart.open}
            editEnabled={user.hasChangePermission(ModelType.supplierpart)}
          />
          <PanelGroup pageKey="supplierpart" panels={panels} />
        </Stack>
      </InstanceDetail>
    </>
  );
}
