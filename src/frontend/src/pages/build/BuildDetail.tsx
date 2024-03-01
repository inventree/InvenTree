import { t } from '@lingui/macro';
import {
  Grid,
  Group,
  LoadingOverlay,
  Skeleton,
  Stack,
  Table
} from '@mantine/core';
import {
  IconClipboardCheck,
  IconClipboardList,
  IconDots,
  IconFileTypePdf,
  IconInfoCircle,
  IconList,
  IconListCheck,
  IconNotes,
  IconPaperclip,
  IconPrinter,
  IconQrcode,
  IconSitemap
} from '@tabler/icons-react';
import { useMemo } from 'react';
import { useParams } from 'react-router-dom';

import { DetailsImage } from '../../components/details/DetailsImage';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import {
  ActionDropdown,
  DuplicateItemAction,
  EditItemAction,
  LinkBarcodeAction,
  UnlinkBarcodeAction,
  ViewBarcodeAction
} from '../../components/items/ActionDropdown';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { StatusRenderer } from '../../components/render/StatusRenderer';
import { NotesEditor } from '../../components/widgets/MarkdownEditor';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { buildOrderFields } from '../../forms/BuildForms';
import { partCategoryFields } from '../../forms/PartForms';
import { useEditApiFormModal } from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { DetailsField, DetailsTable } from '../../tables/Details';
import BuildLineTable from '../../tables/build/BuildLineTable';
import { BuildOrderTable } from '../../tables/build/BuildOrderTable';
import { AttachmentTable } from '../../tables/general/AttachmentTable';
import { StockItemTable } from '../../tables/stock/StockItemTable';

/**
 * Detail page for a single Build Order
 */
export default function BuildDetail() {
  const { id } = useParams();

  const user = useUserState();

  const {
    instance: build,
    refreshInstance,
    instanceQuery
  } = useInstance({
    endpoint: ApiEndpoints.build_order_list,
    pk: id,
    params: {
      part_detail: true
    },
    refetchOnMount: true
  });

  const detailsPanel = useMemo(() => {
    if (instanceQuery.isFetching) {
      return <Skeleton />;
    }

    let tl: DetailsField[] = [
      {
        type: 'link',
        name: 'part',
        label: t`Part`,
        model: ModelType.part
      },
      {
        type: 'status',
        name: 'status',
        label: t`Status`,
        model: ModelType.build
      },
      {
        type: 'text',
        name: 'reference',
        label: t`Reference`
      },
      {
        type: 'text',
        name: 'title',
        label: t`Description`,
        icon: 'description'
      }
    ];

    let tr: DetailsField[] = [
      {
        type: 'text',
        name: 'quantity',
        label: t`Build Quantity`
      },
      {
        type: 'progressbar',
        name: 'completed',
        icon: 'progress',
        total: build.quantity,
        progress: build.completed,
        label: t`Completed Outputs`
      },
      {
        type: 'link',
        name: 'sales_order',
        label: t`Sales Order`,
        icon: 'sales_orders',
        model: ModelType.salesorder,
        model_field: 'reference',
        hidden: !build.sales_order
      },
      {
        type: 'text',
        name: 'issued_by',
        label: t`Issued By`,
        badge: 'user',
        icon: 'user'
      }
    ];

    let bl: DetailsField[] = [
      {
        type: 'text',
        name: 'issued_by',
        label: t`Issued By`
      },
      {
        type: 'text',
        name: 'responsible',
        label: t`Responsible`
      }
    ];

    return (
      <ItemDetailsGrid>
        <Grid>
          <Grid.Col span={4}>
            <DetailsImage
              appRole={UserRoles.part}
              apiPath={ApiEndpoints.part_list}
              src={build.part_detail?.thumbnail}
              pk={build.part}
            />
          </Grid.Col>
          <Grid.Col span={8}>
            <DetailsTable fields={tl} item={build} />
          </Grid.Col>
        </Grid>
        <DetailsTable fields={tr} item={build} />
        <DetailsTable fields={bl} item={build} />
      </ItemDetailsGrid>
    );
  }, [build, instanceQuery]);

  const buildPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'details',
        label: t`Build Details`,
        icon: <IconInfoCircle />,
        content: detailsPanel
      },
      {
        name: 'allocate-stock',
        label: t`Allocate Stock`,
        icon: <IconListCheck />,
        content: build?.pk ? (
          <BuildLineTable
            params={{
              build: id,
              tracked: false
            }}
          />
        ) : (
          <Skeleton />
        )
      },
      {
        name: 'incomplete-outputs',
        label: t`Incomplete Outputs`,
        icon: <IconClipboardList />
        // TODO: Hide if build is complete
      },
      {
        name: 'complete-outputs',
        label: t`Completed Outputs`,
        icon: <IconClipboardCheck />,
        content: (
          <StockItemTable
            params={{
              build: id,
              is_building: false
            }}
          />
        )
      },
      {
        name: 'consumed-stock',
        label: t`Consumed Stock`,
        icon: <IconList />,
        content: (
          <StockItemTable
            params={{
              consumed_by: id
            }}
          />
        )
      },
      {
        name: 'child-orders',
        label: t`Child Build Orders`,
        icon: <IconSitemap />,
        content: build.pk ? (
          <BuildOrderTable parentBuildId={build.pk} />
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
            endpoint={ApiEndpoints.build_order_attachment_list}
            model="build"
            pk={Number(id)}
          />
        )
      },
      {
        name: 'notes',
        label: t`Notes`,
        icon: <IconNotes />,
        content: (
          <NotesEditor
            url={apiUrl(ApiEndpoints.build_order_list, build.pk)}
            data={build.notes ?? ''}
            allowEdit={true}
          />
        )
      }
    ];
  }, [build, id]);

  const editBuild = useEditApiFormModal({
    url: ApiEndpoints.build_order_list,
    pk: build.pk,
    title: t`Edit Build Order`,
    fields: buildOrderFields(),
    onFormSuccess: () => {
      refreshInstance();
    }
  });

  const buildActions = useMemo(() => {
    // TODO: Disable certain actions based on user permissions
    return [
      <ActionDropdown
        key="barcode"
        tooltip={t`Barcode Actions`}
        icon={<IconQrcode />}
        actions={[
          ViewBarcodeAction({}),
          LinkBarcodeAction({
            disabled: build?.barcode_hash
          }),
          UnlinkBarcodeAction({
            disabled: !build?.barcode_hash
          })
        ]}
      />,
      <ActionDropdown
        key="report"
        tooltip={t`Reporting Actions`}
        icon={<IconPrinter />}
        actions={[
          {
            icon: <IconFileTypePdf />,
            name: t`Report`,
            tooltip: t`Print build report`
          }
        ]}
      />,
      <ActionDropdown
        key="build"
        tooltip={t`Build Order Actions`}
        icon={<IconDots />}
        actions={[
          EditItemAction({
            onClick: () => editBuild.open(),
            disabled: !user.hasChangeRole(UserRoles.build)
          }),
          DuplicateItemAction({})
        ]}
      />
    ];
  }, [id, build, user]);

  const buildDetail = useMemo(() => {
    return build?.status ? (
      StatusRenderer({
        status: build.status,
        type: ModelType.build
      })
    ) : (
      <Skeleton />
    );
  }, [build, id]);

  return (
    <>
      {editBuild.modal}
      <Stack spacing="xs">
        <LoadingOverlay visible={instanceQuery.isFetching} />
        <PageDetail
          title={build.reference}
          subtitle={build.title}
          detail={buildDetail}
          imageUrl={build.part_detail?.image ?? build.part_detail?.thumbnail}
          breadcrumbs={[
            { name: t`Build Orders`, url: '/build' },
            { name: build.reference, url: `/build/${build.pk}` }
          ]}
          actions={buildActions}
        />
        <PanelGroup pageKey="build" panels={buildPanels} />
      </Stack>
    </>
  );
}
