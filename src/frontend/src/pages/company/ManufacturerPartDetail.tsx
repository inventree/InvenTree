import { t } from '@lingui/macro';
import { Grid, LoadingOverlay, Skeleton, Stack } from '@mantine/core';
import {
  IconBuildingWarehouse,
  IconDots,
  IconInfoCircle,
  IconList,
  IconPaperclip
} from '@tabler/icons-react';
import { useMemo } from 'react';
import { useParams } from 'react-router-dom';

import { DetailsField, DetailsTable } from '../../components/details/Details';
import { DetailsImage } from '../../components/details/DetailsImage';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import {
  ActionDropdown,
  DeleteItemAction,
  DuplicateItemAction,
  EditItemAction
} from '../../components/items/ActionDropdown';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { useManufacturerPartFields } from '../../forms/CompanyForms';
import { useEditApiFormModal } from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { AttachmentTable } from '../../tables/general/AttachmentTable';
import ManufacturerPartParameterTable from '../../tables/purchasing/ManufacturerPartParameterTable';
import { SupplierPartTable } from '../../tables/purchasing/SupplierPartTable';

export default function ManufacturerPartDetail() {
  const { id } = useParams();
  const user = useUserState();

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

    let data = manufacturerPart ?? {};

    let tl: DetailsField[] = [
      {
        type: 'link',
        name: 'part',
        label: t`Internal Part`,
        model: ModelType.part,
        hidden: !manufacturerPart.part
      },
      {
        type: 'string',
        name: 'description',
        label: t`Description`,
        copy: true,
        hidden: !manufacturerPart.description
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

    let tr: DetailsField[] = [
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
      }
    ];

    return (
      <ItemDetailsGrid>
        <Grid>
          <Grid.Col span={4}>
            <DetailsImage
              appRole={UserRoles.part}
              src={manufacturerPart?.part_detail?.image}
              apiPath={apiUrl(
                ApiEndpoints.part_list,
                manufacturerPart?.part_detail?.pk
              )}
              pk={manufacturerPart?.part_detail?.pk}
            />
          </Grid.Col>
          <Grid.Col span={8}>
            <DetailsTable
              title={t`Manufacturer Part`}
              fields={tl}
              item={data}
            />
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
        name: 'parameters',
        label: t`Parameters`,
        icon: <IconList />,
        content: manufacturerPart?.pk ? (
          <ManufacturerPartParameterTable
            params={{ manufacturer_part: manufacturerPart.pk }}
          />
        ) : (
          <Skeleton />
        )
      },
      {
        name: 'suppliers',
        label: t`Suppliers`,
        icon: <IconBuildingWarehouse />,
        content: manufacturerPart?.pk ? (
          <SupplierPartTable
            params={{
              manufacturer_part: manufacturerPart.pk
            }}
          />
        ) : (
          <Skeleton />
        )
      },
      {
        name: 'attachments',
        label: t`Attachments`,
        icon: <IconPaperclip />,
        content: (
          <AttachmentTable
            endpoint={ApiEndpoints.manufacturer_part_attachment_list}
            model="manufacturer_part"
            pk={manufacturerPart?.pk}
          />
        )
      }
    ];
  }, [manufacturerPart]);

  const editManufacturerPartFields = useManufacturerPartFields();

  const editManufacturerPart = useEditApiFormModal({
    url: ApiEndpoints.manufacturer_part_list,
    pk: manufacturerPart?.pk,
    title: t`Edit Manufacturer Part`,
    fields: editManufacturerPartFields,
    onFormSuccess: refreshInstance
  });

  const manufacturerPartActions = useMemo(() => {
    return [
      <ActionDropdown
        key="part"
        tooltip={t`Manufacturer Part Actions`}
        icon={<IconDots />}
        actions={[
          DuplicateItemAction({
            hidden: !user.hasAddRole(UserRoles.purchase_order)
          }),
          EditItemAction({
            hidden: !user.hasChangeRole(UserRoles.purchase_order),
            onClick: () => editManufacturerPart.open()
          }),
          DeleteItemAction({
            hidden: !user.hasDeleteRole(UserRoles.purchase_order)
          })
        ]}
      />
    ];
  }, [user]);

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
      {editManufacturerPart.modal}
      <Stack spacing="xs">
        <LoadingOverlay visible={instanceQuery.isFetching} />
        <PageDetail
          title={t`ManufacturerPart`}
          subtitle={`${manufacturerPart.MPN} - ${manufacturerPart.part_detail?.name}`}
          breadcrumbs={breadcrumbs}
          actions={manufacturerPartActions}
          imageUrl={manufacturerPart?.part_detail?.thumbnail}
        />
        <PanelGroup pageKey="manufacturerpart" panels={panels} />
      </Stack>
    </>
  );
}
