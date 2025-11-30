import { t } from '@lingui/core/macro';
import { Alert, Grid, Skeleton, Stack, Text } from '@mantine/core';
import {
  IconChecklist,
  IconCircleCheck,
  IconClipboardCheck,
  IconClipboardList,
  IconInfoCircle,
  IconList,
  IconListCheck,
  IconListNumbers,
  IconShoppingCart,
  IconSitemap
} from '@tabler/icons-react';
import { useMemo } from 'react';
import { useParams } from 'react-router-dom';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import { getDetailUrl } from '@lib/functions/Navigation';
import type { ApiFormFieldSet } from '@lib/types/Forms';
import AdminButton from '../../components/buttons/AdminButton';
import PrimaryActionButton from '../../components/buttons/PrimaryActionButton';
import { PrintingActions } from '../../components/buttons/PrintingActions';
import {
  type DetailsField,
  DetailsTable
} from '../../components/details/Details';
import DetailsBadge from '../../components/details/DetailsBadge';
import { DetailsImage } from '../../components/details/DetailsImage';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
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
import AttachmentPanel from '../../components/panels/AttachmentPanel';
import NotesPanel from '../../components/panels/NotesPanel';
import type { PanelType } from '../../components/panels/Panel';
import { PanelGroup } from '../../components/panels/PanelGroup';
import ParametersPanel from '../../components/panels/ParametersPanel';
import { StatusRenderer } from '../../components/render/StatusRenderer';
import { RenderStockLocation } from '../../components/render/Stock';
import { useBuildOrderFields } from '../../forms/BuildForms';
import {
  useCreateApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import useStatusCodes from '../../hooks/UseStatusCodes';
import { useGlobalSettingsState } from '../../states/SettingsStates';
import { useUserState } from '../../states/UserState';
import BuildAllocatedStockTable from '../../tables/build/BuildAllocatedStockTable';
import BuildLineTable from '../../tables/build/BuildLineTable';
import { BuildOrderTable } from '../../tables/build/BuildOrderTable';
import BuildOutputTable from '../../tables/build/BuildOutputTable';
import PartTestResultTable from '../../tables/part/PartTestResultTable';
import { PurchaseOrderTable } from '../../tables/purchasing/PurchaseOrderTable';
import { StockItemTable } from '../../tables/stock/StockItemTable';

function NoItems() {
  return (
    <Alert color='blue' icon={<IconInfoCircle />} title={t`No Required Items`}>
      <Stack gap='xs'>
        <Text>{t`This build order does not have any required items.`}</Text>
        <Text>{t`The assembled part may not have a Bill of Materials (BOM) defined, or the BOM is empty.`}</Text>
      </Stack>
    </Alert>
  );
}

/**
 * Panel to display the lines of a build order
 */
function BuildLinesPanel({
  build,
  isLoading,
  hasItems
}: Readonly<{
  build: any;
  isLoading: boolean;
  hasItems: boolean;
}>) {
  const buildLocation = useInstance({
    endpoint: ApiEndpoints.stock_location_list,
    pk: build?.take_from,
    hasPrimaryKey: true,
    defaultValue: {}
  });

  if (isLoading || !build.pk) {
    return <Skeleton w={'100%'} h={400} animate />;
  }

  if (!hasItems) {
    return <NoItems />;
  }

  return (
    <Stack gap='xs'>
      {buildLocation.instance.pk && (
        <Alert color='blue' icon={<IconSitemap />} title={t`Source Location`}>
          <RenderStockLocation instance={buildLocation.instance} />
        </Alert>
      )}
      <BuildLineTable build={build} />
    </Stack>
  );
}

function BuildAllocationsPanel({
  build,
  isLoading,
  hasItems
}: Readonly<{
  build: any;
  isLoading: boolean;
  hasItems: boolean;
}>) {
  if (isLoading || !build.pk) {
    return <Skeleton w={'100%'} h={400} animate />;
  }

  if (!hasItems) {
    return <NoItems />;
  }

  return <BuildAllocatedStockTable buildId={build.pk} showPartInfo allowEdit />;
}

/**
 * Detail page for a single Build Order
 */
export default function BuildDetail() {
  const { id } = useParams();

  const user = useUserState();
  const globalSettings = useGlobalSettingsState();

  // Fetch the number of BOM items associated with the build order
  const { instance: buildLineData, instanceQuery: buildLineQuery } =
    useInstance({
      endpoint: ApiEndpoints.build_line_list,
      params: {
        build: id,
        allocations: false,
        part_detail: false,
        build_detail: false,
        bom_item_detail: false,
        limit: 1
      },
      disabled: !id,
      hasPrimaryKey: false,
      defaultValue: {}
    });

  const buildStatus = useStatusCodes({ modelType: ModelType.build });

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

  const { instance: partRequirements, instanceQuery: partRequirementsQuery } =
    useInstance({
      endpoint: ApiEndpoints.part_requirements,
      pk: build?.part,
      hasPrimaryKey: true,
      defaultValue: {}
    });

  const detailsPanel = useMemo(() => {
    if (instanceQuery.isFetching) {
      return <Skeleton />;
    }

    const data = {
      ...build,
      can_build: partRequirements?.can_build ?? 0
    };

    const tl: DetailsField[] = [
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
        type: 'string',
        name: 'part_detail.revision',
        icon: 'revision',
        label: t`Revision`,
        hidden: !build.part_detail?.revision,
        copy: true
      },
      {
        type: 'status',
        name: 'status',
        label: t`Status`,
        model: ModelType.build
      },
      {
        type: 'status',
        name: 'status_custom_key',
        label: t`Custom Status`,
        model: ModelType.build,
        icon: 'status',
        hidden:
          !build.status_custom_key || build.status_custom_key == build.status
      },
      {
        type: 'boolean',
        name: 'external',
        label: t`External`,
        icon: 'manufacturers',
        hidden: !build.external
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

    const tr: DetailsField[] = [
      {
        type: 'number',
        name: 'quantity',
        label: t`Build Quantity`
      },
      {
        type: 'number',
        name: 'can_build',
        unit: build.part_detail?.units,
        label: t`Can Build`,
        hidden: partRequirementsQuery.isFetching
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

    const bl: DetailsField[] = [
      {
        type: 'text',
        name: 'issued_by',
        label: t`Issued By`,
        icon: 'user',
        badge: 'user',
        hidden: !build.issued_by
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
        name: 'project_code_label',
        label: t`Project Code`,
        icon: 'reference',
        copy: true,
        hidden: !build.project_code
      },
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

    const br: DetailsField[] = [
      {
        type: 'date',
        name: 'creation_date',
        label: t`Created`,
        icon: 'calendar',
        copy: true,
        hidden: !build.creation_date
      },
      {
        type: 'date',
        name: 'start_date',
        label: t`Start Date`,
        icon: 'calendar',
        copy: true,
        hidden: !build.start_date
      },
      {
        type: 'date',
        name: 'target_date',
        label: t`Target Date`,
        icon: 'calendar',
        copy: true,
        hidden: !build.target_date
      },
      {
        type: 'date',
        name: 'completion_date',
        label: t`Completed`,
        icon: 'calendar',
        copy: true,
        hidden: !build.completion_date
      }
    ];

    return (
      <ItemDetailsGrid>
        <Grid grow>
          <DetailsImage
            appRole={UserRoles.part}
            apiPath={ApiEndpoints.part_list}
            src={build.part_detail?.image ?? build.part_detail?.thumbnail}
            pk={build.part}
          />
          <Grid.Col span={{ base: 12, sm: 8 }}>
            <DetailsTable fields={tl} item={data} />
          </Grid.Col>
        </Grid>
        <DetailsTable fields={tr} item={data} />
        <DetailsTable fields={bl} item={data} />
        <DetailsTable fields={br} item={data} />
      </ItemDetailsGrid>
    );
  }, [
    build,
    instanceQuery,
    partRequirements,
    partRequirementsQuery.isFetching
  ]);

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
        label: t`Required Parts`,
        icon: <IconListNumbers />,
        content: (
          <BuildLinesPanel
            build={build}
            isLoading={buildLineQuery.isFetching || buildLineQuery.isLoading}
            hasItems={buildLineData?.count > 0}
          />
        )
      },
      {
        name: 'allocated-stock',
        label: t`Allocated Stock`,
        icon: <IconList />,
        hidden:
          build.status == buildStatus.COMPLETE ||
          build.status == buildStatus.CANCELLED ||
          (buildLineData?.count ?? 0) <= 0, // Hide if no required parts
        content: (
          <BuildAllocationsPanel
            build={build}
            isLoading={buildLineQuery.isFetching || buildLineQuery.isLoading}
            hasItems={buildLineData?.count > 0}
          />
        )
      },
      {
        name: 'consumed-stock',
        label: t`Consumed Stock`,
        icon: <IconListCheck />,
        hidden: (buildLineData?.count ?? 0) <= 0, // Hide if no required parts
        content: (
          <StockItemTable
            allowAdd={false}
            tableName='build-consumed'
            showLocation={false}
            allowReturn
            params={{
              consumed_by: id
            }}
          />
        )
      },
      {
        name: 'incomplete-outputs',
        label: t`Incomplete Outputs`,
        icon: <IconClipboardList />,
        content: build.pk ? (
          <BuildOutputTable build={build} refreshBuild={refreshInstance} />
        ) : (
          <Skeleton />
        ),
        hidden:
          build.status == buildStatus.COMPLETE ||
          build.status == buildStatus.CANCELLED
      },
      {
        name: 'complete-outputs',
        label: t`Completed Outputs`,
        icon: <IconClipboardCheck />,
        content: (
          <StockItemTable
            allowAdd={false}
            tableName='completed-build-outputs'
            params={{
              build: id,
              is_building: false
            }}
          />
        )
      },
      {
        name: 'external-purchase-orders',
        label: t`External Orders`,
        icon: <IconShoppingCart />,
        content: build.pk ? (
          <PurchaseOrderTable externalBuildId={build.pk} />
        ) : (
          <Skeleton />
        ),
        hidden:
          !user.hasViewRole(UserRoles.purchase_order) ||
          !build.external ||
          !globalSettings.isSet('BUILDORDER_EXTERNAL_BUILDS')
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
          <PartTestResultTable buildId={build.pk} partId={build.part} />
        ) : (
          <Skeleton />
        )
      },
      ParametersPanel({
        model_type: ModelType.build,
        model_id: build.pk
      }),
      AttachmentPanel({
        model_type: ModelType.build,
        model_id: build.pk
      }),
      NotesPanel({
        model_type: ModelType.build,
        model_id: build.pk
      })
    ];
  }, [
    build,
    id,
    user,
    buildStatus,
    globalSettings,
    buildLineQuery.isFetching,
    buildLineQuery.isLoading,
    buildLineData
  ]);

  const editBuildOrderFields = useBuildOrderFields({
    create: false,
    modalId: 'edit-build-order'
  });

  const editBuild = useEditApiFormModal({
    url: ApiEndpoints.build_order_list,
    pk: build.pk,
    title: t`Edit Build Order`,
    modalId: 'edit-build-order',
    fields: editBuildOrderFields,
    onFormSuccess: refreshInstance
  });

  const duplicateBuildOrderInitialData = useMemo(() => {
    const data = { ...build };
    // if we set the reference to null/undefined, it will be left blank in the form
    // if we omit the reference altogether, it will be auto-generated via reference pattern
    // from the OPTIONS response
    delete data.reference;
    return data;
  }, [build]);

  const duplicateBuildOrderFields = useBuildOrderFields({
    create: false,
    modalId: 'duplicate-build-order'
  });

  const duplicateBuild = useCreateApiFormModal({
    url: ApiEndpoints.build_order_list,
    title: t`Add Build Order`,
    modalId: 'duplicate-build-order',
    fields: duplicateBuildOrderFields,
    initialData: duplicateBuildOrderInitialData,
    follow: true,
    modelType: ModelType.build
  });

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

  const completeOrderFields: ApiFormFieldSet = useMemo(() => {
    const hasBom = (buildLineData?.count ?? 0) > 0;

    return {
      accept_overallocated: {
        hidden: !hasBom
      },
      accept_unallocated: {
        hidden: !hasBom
      },
      accept_incomplete: {}
    };
  }, [buildLineData.count]);

  const completeOrder = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.build_order_complete, build.pk),
    title: t`Complete Build Order`,
    onFormSuccess: refreshInstance,
    preFormContent: (
      <Alert
        color='green'
        icon={<IconCircleCheck />}
        title={t`Mark this order as complete`}
      />
    ),
    successMessage: t`Order completed`,
    fields: completeOrderFields
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
        icon='issue'
        hidden={!canIssue}
        color='blue'
        onClick={issueOrder.open}
      />,
      <PrimaryActionButton
        title={t`Complete Order`}
        icon='complete'
        hidden={!canComplete}
        color='green'
        onClick={completeOrder.open}
      />,
      <AdminButton model={ModelType.build} id={build.pk} />,
      <BarcodeActionDropdown
        model={ModelType.build}
        pk={build.pk}
        hash={build?.barcode_hash}
      />,
      <PrintingActions
        modelType={ModelType.build}
        items={[build.pk]}
        enableLabels
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
          />,
          <DetailsBadge
            label={t`External`}
            color='blue'
            key='external'
            visible={build.external}
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
      <InstanceDetail query={instanceQuery} requiredRole={UserRoles.build}>
        <Stack gap='xs'>
          <PageDetail
            title={`${t`Build Order`}: ${build.reference}`}
            subtitle={`${build.quantity} x ${build.part_detail?.full_name}`}
            badges={buildBadges}
            editAction={editBuild.open}
            editEnabled={user.hasChangePermission(ModelType.part)}
            imageUrl={build.part_detail?.image ?? build.part_detail?.thumbnail}
            breadcrumbs={[{ name: t`Manufacturing`, url: '/manufacturing' }]}
            lastCrumb={[
              {
                name: build.reference,
                url: getDetailUrl(ModelType.build, build.pk)
              }
            ]}
            actions={buildActions}
          />
          <PanelGroup
            pageKey='build'
            panels={buildPanels}
            instance={build}
            reloadInstance={refreshInstance}
            model={ModelType.build}
            id={build.pk}
          />
        </Stack>
      </InstanceDetail>
    </>
  );
}
