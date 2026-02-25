import { t } from '@lingui/core/macro';
import { Grid, Skeleton, Stack } from '@mantine/core';
import {
  IconBuildingWarehouse,
  IconInfoCircle,
  IconPackages
} from '@tabler/icons-react';
import { useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import { getDetailUrl } from '@lib/functions/Navigation';
import AdminButton from '../../components/buttons/AdminButton';
import {
  type DetailsField,
  DetailsTable
} from '../../components/details/Details';
import { DetailsImage } from '../../components/details/DetailsImage';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import {
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
import { useManufacturerPartFields } from '../../forms/CompanyForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import { useUserState } from '../../states/UserState';
import { SupplierPartTable } from '../../tables/purchasing/SupplierPartTable';
import { StockItemTable } from '../../tables/stock/StockItemTable';

export default function ManufacturerPartDetail() {
  const { id } = useParams();
  const user = useUserState();
  const navigate = useNavigate();

  const {
    instance: manufacturerPart,
    instanceQuery,
    refreshInstance
  } = useInstance({
    endpoint: ApiEndpoints.manufacturer_part_list,
    pk: id,
    hasPrimaryKey: true,
    params: {
      part_detail: true,
      manufacturer_detail: true
    }
  });

  const detailsPanel = useMemo(() => {
    if (instanceQuery.isFetching) {
      return <Skeleton />;
    }

    const data = manufacturerPart ?? {};

    const tl: DetailsField[] = [
      {
        type: 'link',
        name: 'part',
        label: t`Internal Part`,
        model: ModelType.part,
        hidden: !manufacturerPart.part
      },
      {
        type: 'string',
        name: 'part_detail.IPN',
        label: t`IPN`,
        copy: true,
        icon: 'serial',
        hidden: !data.part_detail?.IPN
      },
      {
        type: 'string',
        name: 'part_detail.description',
        label: t`Description`,
        copy: true,
        icon: 'info',
        hidden: !manufacturerPart.description
      }
    ];

    const tr: DetailsField[] = [
      {
        type: 'link',
        name: 'manufacturer',
        label: t`Manufacturer`,
        icon: 'manufacturers',
        model: ModelType.company,
        hidden: !manufacturerPart.manufacturer
      },
      {
        type: 'string',
        name: 'MPN',
        label: t`Manufacturer Part Number`,
        copy: true,
        hidden: !manufacturerPart.MPN,
        icon: 'reference'
      },
      {
        type: 'string',
        name: 'description',
        label: t`Description`,
        copy: true,
        hidden: !manufacturerPart.description,
        icon: 'info'
      },
      {
        type: 'link',
        external: true,
        name: 'link',
        label: t`External Link`,
        copy: true,
        hidden: !manufacturerPart.link
      }
    ];

    return (
      <ItemDetailsGrid>
        <Grid grow>
          <DetailsImage
            appRole={UserRoles.part}
            src={manufacturerPart?.part_detail?.image}
            apiPath={apiUrl(
              ApiEndpoints.part_list,
              manufacturerPart?.part_detail?.pk
            )}
            pk={manufacturerPart?.part_detail?.pk}
          />
          <Grid.Col span={{ base: 12, sm: 8 }}>
            <DetailsTable title={t`Part Details`} fields={tl} item={data} />
          </Grid.Col>
        </Grid>
        <DetailsTable title={t`Manufacturer Details`} fields={tr} item={data} />
      </ItemDetailsGrid>
    );
  }, [manufacturerPart, instanceQuery]);

  const panels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'details',
        label: t`Manufacturer Part Details`,
        icon: <IconInfoCircle />,
        content: detailsPanel
      },
      {
        name: 'stock',
        label: t`Received Stock`,
        hidden: !user.hasViewRole(UserRoles.stock),
        icon: <IconPackages />,
        content: (
          <StockItemTable
            tableName='manufacturer-part-stock'
            params={{
              manufacturer_part: id
            }}
          />
        )
      },
      {
        name: 'suppliers',
        label: t`Suppliers`,
        icon: <IconBuildingWarehouse />,
        content: manufacturerPart?.pk ? (
          <SupplierPartTable
            partId={manufacturerPart.part}
            manufacturerId={manufacturerPart.manufacturer}
            manufacturerPartId={manufacturerPart.pk}
          />
        ) : (
          <Skeleton />
        )
      },
      ParametersPanel({
        model_type: ModelType.manufacturerpart,
        model_id: manufacturerPart?.pk
      }),
      AttachmentPanel({
        model_type: ModelType.manufacturerpart,
        model_id: manufacturerPart?.pk
      }),
      NotesPanel({
        model_type: ModelType.manufacturerpart,
        model_id: manufacturerPart?.pk,
        has_note: !!manufacturerPart?.notes
      })
    ];
  }, [user, manufacturerPart]);

  const editManufacturerPartFields = useManufacturerPartFields();

  const editManufacturerPart = useEditApiFormModal({
    url: ApiEndpoints.manufacturer_part_list,
    pk: manufacturerPart?.pk,
    title: t`Edit Manufacturer Part`,
    fields: editManufacturerPartFields,
    onFormSuccess: refreshInstance
  });

  const duplicateManufacturerPart = useCreateApiFormModal({
    url: ApiEndpoints.manufacturer_part_list,
    title: t`Add Manufacturer Part`,
    fields: editManufacturerPartFields,
    initialData: {
      ...manufacturerPart
    },
    follow: true,
    modelType: ModelType.manufacturerpart
  });

  const deleteManufacturerPart = useDeleteApiFormModal({
    url: ApiEndpoints.manufacturer_part_list,
    pk: manufacturerPart?.pk,
    title: t`Delete Manufacturer Part`,
    onFormSuccess: () => {
      navigate(getDetailUrl(ModelType.part, manufacturerPart.part));
    }
  });

  const manufacturerPartActions = useMemo(() => {
    return [
      <AdminButton
        key='admin'
        model={ModelType.manufacturerpart}
        id={manufacturerPart.pk}
      />,
      <OptionsActionDropdown
        key='options'
        tooltip={t`Manufacturer Part Actions`}
        actions={[
          DuplicateItemAction({
            hidden: !user.hasAddRole(UserRoles.purchase_order),
            onClick: () => duplicateManufacturerPart.open()
          }),
          EditItemAction({
            hidden: !user.hasChangeRole(UserRoles.purchase_order),
            onClick: () => editManufacturerPart.open()
          }),
          DeleteItemAction({
            hidden: !user.hasDeleteRole(UserRoles.purchase_order),
            onClick: () => deleteManufacturerPart.open()
          })
        ]}
      />
    ];
  }, [user, manufacturerPart]);

  const breadcrumbs = useMemo(() => {
    return [
      {
        name: t`Purchasing`,
        url: '/purchasing/'
      },
      {
        name: manufacturerPart?.manufacturer_detail?.name ?? t`Manufacturer`,
        url: `/purchasing/manufacturer/${manufacturerPart?.manufacturer_detail?.pk}/`
      }
    ];
  }, [manufacturerPart]);

  return (
    <>
      {deleteManufacturerPart.modal}
      {duplicateManufacturerPart.modal}
      {editManufacturerPart.modal}
      <InstanceDetail
        query={instanceQuery}
        requiredPermission={ModelType.manufacturerpart}
      >
        <Stack gap='xs'>
          <PageDetail
            title={t`Manufacturer Part`}
            subtitle={`${manufacturerPart.MPN} - ${manufacturerPart.part_detail?.name}`}
            breadcrumbs={breadcrumbs}
            lastCrumb={[
              {
                name: manufacturerPart.MPN,
                url: getDetailUrl(
                  ModelType.manufacturerpart,
                  manufacturerPart.pk
                )
              }
            ]}
            actions={manufacturerPartActions}
            imageUrl={manufacturerPart?.part_detail?.thumbnail}
            editAction={editManufacturerPart.open}
            editEnabled={user.hasChangePermission(ModelType.manufacturerpart)}
          />
          <PanelGroup
            pageKey='manufacturerpart'
            panels={panels}
            instance={manufacturerPart}
            reloadInstance={refreshInstance}
            model={ModelType.manufacturerpart}
            id={manufacturerPart.pk}
          />
        </Stack>
      </InstanceDetail>
    </>
  );
}
