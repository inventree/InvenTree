import { t } from '@lingui/macro';
import { Grid, Skeleton, Stack } from '@mantine/core';
import {
  IconClipboardCheck,
  IconClipboardList,
  IconDots,
  IconInfoCircle,
  IconList,
  IconListCheck,
  IconNotes,
  IconPaperclip,
  IconQrcode,
  IconSitemap
} from '@tabler/icons-react';
import { useMemo } from 'react';
import { useParams } from 'react-router-dom';

import AdminButton from '../../components/buttons/AdminButton';
import { PrintingActions } from '../../components/buttons/PrintingActions';
import { DetailsField, DetailsTable } from '../../components/details/Details';
import { DetailsImage } from '../../components/details/DetailsImage';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import NotesEditor from '../../components/editors/NotesEditor';
import {
  ActionDropdown,
  CancelItemAction,
  DuplicateItemAction,
  EditItemAction,
  LinkBarcodeAction,
  UnlinkBarcodeAction,
  ViewBarcodeAction
} from '../../components/items/ActionDropdown';
import InstanceDetail from '../../components/nav/InstanceDetail';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { StatusRenderer } from '../../components/render/StatusRenderer';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { useBuildOrderFields } from '../../forms/BuildForms';
import {
  useCreateApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import BuildLineTable from '../../tables/build/BuildLineTable';
import { BuildOrderTable } from '../../tables/build/BuildOrderTable';
import BuildOutputTable from '../../tables/build/BuildOutputTable';
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
    instanceQuery,
    requestStatus
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
      },
      {
        type: 'link',
        name: 'parent',
        icon: 'builds',
        label: t`Parent Build`,
        model_field: 'reference',
        model: ModelType.build,
        hidden: !build.parent
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
      }
    ];

    let bl: DetailsField[] = [
      {
        type: 'text',
        name: 'issued_by',
        label: t`Issued By`,
        icon: 'user',
        badge: 'user'
      },
      {
        type: 'text',
        name: 'responsible',
        label: t`Responsible`,
        badge: 'owner',
        hidden: !build.responsible
      },
      {
        type: 'text',
        name: 'creation_date',
        label: t`Created`,
        icon: 'calendar',
        hidden: !build.creation_date
      },
      {
        type: 'text',
        name: 'target_date',
        label: t`Target Date`,
        icon: 'calendar',
        hidden: !build.target_date
      },
      {
        type: 'text',
        name: 'completion_date',
        label: t`Completed`,
        icon: 'calendar',
        hidden: !build.completion_date
      }
    ];

    let br: DetailsField[] = [
      {
        type: 'link',
        name: 'take_from',
        icon: 'location',
        model: ModelType.stocklocation,
        label: t`Source Location`,
        backup_value: t`Any location`
      },
      {
        type: 'link',
        name: 'destination',
        icon: 'location',
        model: ModelType.stocklocation,
        label: t`Destination Location`,
        hidden: !build.destination
      },
      {
        type: 'text',
        name: 'batch',
        label: t`Batch Code`,
        hidden: !build.batch,
        copy: true
      }
    ];

    return (
      <ItemDetailsGrid>
        <Grid>
          <Grid.Col span={4}>
            <DetailsImage
              appRole={UserRoles.part}
              apiPath={ApiEndpoints.part_list}
              src={build.part_detail?.image ?? build.part_detail?.thumbnail}
              pk={build.part}
            />
          </Grid.Col>
          <Grid.Col span={8}>
            <DetailsTable fields={tl} item={build} />
          </Grid.Col>
        </Grid>
        <DetailsTable fields={tr} item={build} />
        <DetailsTable fields={bl} item={build} />
        <DetailsTable fields={br} item={build} />
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
              build: id
            }}
          />
        ) : (
          <Skeleton />
        )
      },
      {
        name: 'incomplete-outputs',
        label: t`Incomplete Outputs`,
        icon: <IconClipboardList />,
        content: build.pk ? <BuildOutputTable build={build} /> : <Skeleton />
        // TODO: Hide if build is complete
      },
      {
        name: 'complete-outputs',
        label: t`Completed Outputs`,
        icon: <IconClipboardCheck />,
        content: (
          <StockItemTable
            allowAdd={false}
            tableName="build-outputs"
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
            allowAdd={false}
            tableName="build-consumed"
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
          <AttachmentTable model_type={ModelType.build} model_id={Number(id)} />
        )
      },
      {
        name: 'notes',
        label: t`Notes`,
        icon: <IconNotes />,
        content: (
          <NotesEditor
            modelType={ModelType.build}
            modelId={build.pk}
            editable={user.hasChangeRole(UserRoles.build)}
          />
        )
      }
    ];
  }, [build, id, user]);

  const buildOrderFields = useBuildOrderFields({ create: false });

  const editBuild = useEditApiFormModal({
    url: ApiEndpoints.build_order_list,
    pk: build.pk,
    title: t`Edit Build Order`,
    fields: buildOrderFields,
    onFormSuccess: () => {
      refreshInstance();
    }
  });

  const cancelBuild = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.build_order_cancel, build.pk),
    title: t`Cancel Build Order`,
    fields: {
      remove_allocated_stock: {},
      remove_incomplete_outputs: {}
    },
    onFormSuccess: () => {
      refreshInstance();
    }
  });

  const duplicateBuild = useCreateApiFormModal({
    url: ApiEndpoints.build_order_list,
    title: t`Add Build Order`,
    fields: buildOrderFields,
    initialData: {
      ...build,
      reference: undefined
    },
    follow: true,
    modelType: ModelType.build
  });

  const buildActions = useMemo(() => {
    return [
      <AdminButton model={ModelType.build} pk={build.pk} />,
      <ActionDropdown
        tooltip={t`Barcode Actions`}
        icon={<IconQrcode />}
        actions={[
          ViewBarcodeAction({}),
          LinkBarcodeAction({
            hidden: build?.barcode_hash
          }),
          UnlinkBarcodeAction({
            hidden: !build?.barcode_hash
          })
        ]}
      />,
      <PrintingActions
        modelType={ModelType.build}
        items={[build.pk]}
        enableReports
      />,
      <ActionDropdown
        tooltip={t`Build Order Actions`}
        icon={<IconDots />}
        actions={[
          EditItemAction({
            onClick: () => editBuild.open(),
            hidden: !user.hasChangeRole(UserRoles.build)
          }),
          CancelItemAction({
            tooltip: t`Cancel order`,
            onClick: () => cancelBuild.open(),
            hidden: !user.hasChangeRole(UserRoles.build)
            // TODO: Hide if build cannot be cancelled
          }),
          DuplicateItemAction({
            onClick: () => duplicateBuild.open(),
            hidden: !user.hasAddRole(UserRoles.build)
          })
        ]}
      />
    ];
  }, [id, build, user]);

  const buildBadges = useMemo(() => {
    return instanceQuery.isFetching
      ? []
      : [
          <StatusRenderer
            status={build.status}
            type={ModelType.build}
            options={{ size: 'lg' }}
          />
        ];
  }, [build, instanceQuery]);

  return (
    <>
      {editBuild.modal}
      {duplicateBuild.modal}
      {cancelBuild.modal}
      <InstanceDetail status={requestStatus} loading={instanceQuery.isFetching}>
        <Stack gap="xs">
          <PageDetail
            title={build.reference}
            subtitle={build.title}
            badges={buildBadges}
            imageUrl={build.part_detail?.image ?? build.part_detail?.thumbnail}
            breadcrumbs={[
              { name: t`Build Orders`, url: '/build' },
              { name: build.reference, url: `/build/${build.pk}` }
            ]}
            actions={buildActions}
          />
          <PanelGroup pageKey="build" panels={buildPanels} />
        </Stack>
      </InstanceDetail>
    </>
  );
}
