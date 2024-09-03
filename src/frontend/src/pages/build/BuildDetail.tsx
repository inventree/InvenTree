import { t } from '@lingui/macro';
import { Grid, Skeleton, Stack } from '@mantine/core';
import {
  IconChecklist,
  IconClipboardCheck,
  IconClipboardList,
  IconInfoCircle,
  IconList,
  IconListCheck,
  IconListNumbers,
  IconNotes,
  IconPaperclip,
  IconReportAnalytics,
  IconSitemap
} from '@tabler/icons-react';
import { useMemo } from 'react';
import { useParams } from 'react-router-dom';

import AdminButton from '../../components/buttons/AdminButton';
import PrimaryActionButton from '../../components/buttons/PrimaryActionButton';
import { PrintingActions } from '../../components/buttons/PrintingActions';
import { DetailsField, DetailsTable } from '../../components/details/Details';
import { DetailsImage } from '../../components/details/DetailsImage';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import NotesEditor from '../../components/editors/NotesEditor';
import {
  BarcodeActionDropdown,
  CancelItemAction,
  DuplicateItemAction,
  EditItemAction,
  HoldItemAction,
  OptionsActionDropdown
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
import useStatusCodes from '../../hooks/UseStatusCodes';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import BuildAllocatedStockTable from '../../tables/build/BuildAllocatedStockTable';
import BuildLineTable from '../../tables/build/BuildLineTable';
import { BuildOrderTable } from '../../tables/build/BuildOrderTable';
import BuildOrderTestTable from '../../tables/build/BuildOrderTestTable';
import BuildOutputTable from '../../tables/build/BuildOutputTable';
import { AttachmentTable } from '../../tables/general/AttachmentTable';
import { StockItemTable } from '../../tables/stock/StockItemTable';
import { TestStatisticsTable } from '../../tables/stock/TestStatisticsTable';

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
        type: 'text',
        name: 'part_detail.IPN',
        icon: 'part',
        label: t`IPN`,
        hidden: !build.part_detail?.IPN,
        copy: true
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
        label: t`Reference`,
        copy: true
      },
      {
        type: 'text',
        name: 'title',
        label: t`Description`,
        icon: 'description',
        copy: true
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
        name: 'line-items',
        label: t`Line Items`,
        icon: <IconListNumbers />,
        content: build?.pk ? (
          <BuildLineTable build={build} buildId={build.pk} />
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
        name: 'allocated-stock',
        label: t`Allocated Stock`,
        icon: <IconList />,
        content: build.pk ? (
          <BuildAllocatedStockTable buildId={build.pk} showPartInfo allowEdit />
        ) : (
          <Skeleton />
        )
      },
      {
        name: 'consumed-stock',
        label: t`Consumed Stock`,
        icon: <IconListCheck />,
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
        name: 'test-results',
        label: t`Test Results`,
        icon: <IconChecklist />,
        hidden: !build.part_detail?.testable,
        content: build.pk ? (
          <BuildOrderTestTable buildId={build.pk} partId={build.part} />
        ) : (
          <Skeleton />
        )
      },
      {
        name: 'test-statistics',
        label: t`Test Statistics`,
        icon: <IconReportAnalytics />,
        content: (
          <TestStatisticsTable
            params={{
              pk: build.pk,
              apiEndpoint: ApiEndpoints.build_test_statistics
            }}
          />
        ),
        hidden: !build?.part_detail?.testable
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
    onFormSuccess: refreshInstance
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

  const buildStatus = useStatusCodes({ modelType: ModelType.build });

  const cancelOrder = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.build_order_cancel, build.pk),
    title: t`Cancel Build Order`,
    onFormSuccess: refreshInstance,
    successMessage: t`Order cancelled`,
    preFormWarning: t`Cancel this order`,
    fields: {
      remove_allocated_stock: {},
      remove_incomplete_outputs: {}
    }
  });

  const holdOrder = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.build_order_hold, build.pk),
    title: t`Hold Build Order`,
    onFormSuccess: refreshInstance,
    preFormWarning: t`Place this order on hold`,
    successMessage: t`Order placed on hold`
  });

  const issueOrder = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.build_order_issue, build.pk),
    title: t`Issue Build Order`,
    onFormSuccess: refreshInstance,
    preFormWarning: t`Issue this order`,
    successMessage: t`Order issued`
  });

  const completeOrder = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.build_order_complete, build.pk),
    title: t`Complete Build Order`,
    onFormSuccess: refreshInstance,
    preFormWarning: t`Mark this order as complete`,
    successMessage: t`Order completed`,
    fields: {
      accept_overallocated: {},
      accept_unallocated: {},
      accept_incomplete: {}
    }
  });

  const buildActions = useMemo(() => {
    const canEdit = user.hasChangeRole(UserRoles.build);

    const canIssue =
      canEdit &&
      (build.status == buildStatus.PENDING ||
        build.status == buildStatus.ON_HOLD);

    const canComplete = canEdit && build.status == buildStatus.PRODUCTION;

    const canHold =
      canEdit &&
      (build.status == buildStatus.PENDING ||
        build.status == buildStatus.PRODUCTION);

    const canCancel =
      canEdit &&
      (build.status == buildStatus.PENDING ||
        build.status == buildStatus.ON_HOLD ||
        build.status == buildStatus.PRODUCTION);

    return [
      <PrimaryActionButton
        title={t`Issue Order`}
        icon="issue"
        hidden={!canIssue}
        color="blue"
        onClick={issueOrder.open}
      />,
      <PrimaryActionButton
        title={t`Complete Order`}
        icon="complete"
        hidden={!canComplete}
        color="green"
        onClick={completeOrder.open}
      />,
      <AdminButton model={ModelType.build} pk={build.pk} />,
      <BarcodeActionDropdown
        model={ModelType.build}
        pk={build.pk}
        hash={build?.barcode_hash}
      />,
      <PrintingActions
        modelType={ModelType.build}
        items={[build.pk]}
        enableReports
      />,
      <OptionsActionDropdown
        tooltip={t`Build Order Actions`}
        actions={[
          EditItemAction({
            onClick: () => editBuild.open(),
            hidden: !canEdit,
            tooltip: t`Edit order`
          }),
          DuplicateItemAction({
            onClick: () => duplicateBuild.open(),
            tooltip: t`Duplicate order`,
            hidden: !user.hasAddRole(UserRoles.build)
          }),
          HoldItemAction({
            tooltip: t`Hold order`,
            hidden: !canHold,
            onClick: holdOrder.open
          }),
          CancelItemAction({
            tooltip: t`Cancel order`,
            onClick: cancelOrder.open,
            hidden: !canCancel
          })
        ]}
      />
    ];
  }, [id, build, user, buildStatus]);

  const buildBadges = useMemo(() => {
    return instanceQuery.isFetching
      ? []
      : [
          <StatusRenderer
            status={build.status_custom_key}
            type={ModelType.build}
            options={{ size: 'lg' }}
          />
        ];
  }, [build, instanceQuery]);

  return (
    <>
      {editBuild.modal}
      {duplicateBuild.modal}
      {cancelOrder.modal}
      {holdOrder.modal}
      {issueOrder.modal}
      {completeOrder.modal}
      <InstanceDetail status={requestStatus} loading={instanceQuery.isFetching}>
        <Stack gap="xs">
          <PageDetail
            title={build.reference}
            subtitle={build.title}
            badges={buildBadges}
            editAction={editBuild.open}
            editEnabled={user.hasChangePermission(ModelType.part)}
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
