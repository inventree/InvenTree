import { t } from '@lingui/core/macro';
import { Alert, Stack } from '@mantine/core';
import { IconCircleCheck, IconInfoCircle, IconList } from '@tabler/icons-react';
import { type ReactNode, useMemo } from 'react';
import { useParams } from 'react-router-dom';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { PanelType } from '@lib/types/Panel';
import AdminButton from '../../components/buttons/AdminButton';
import PrimaryActionButton from '../../components/buttons/PrimaryActionButton';
import { PrintingActions } from '../../components/buttons/PrintingActions';
import {
  BarcodeActionDropdown,
  CancelItemAction,
  EditItemAction,
  OptionsActionDropdown
} from '../../components/items/ActionDropdown';
import InstanceDetail from '../../components/nav/InstanceDetail';
import { PageDetail } from '../../components/nav/PageDetail';
import AttachmentPanel from '../../components/panels/AttachmentPanel';
import NotesPanel from '../../components/panels/NotesPanel';
import { PanelGroup } from '../../components/panels/PanelGroup';
import ParametersPanel from '../../components/panels/ParametersPanel';
import { StatusRenderer } from '../../components/render/StatusRenderer';
import { useNonConformanceFields } from '../../forms/NCRForms';
import {
  useCreateApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import useStatusCodes from '../../hooks/UseStatusCodes';
import { useUserState } from '../../states/UserState';
import NonConformanceStockItemTable from '../../tables/build/NonConformanceStockItemTable';
import { NonConformanceDetailsPanel } from './NonConformanceDetailsPanel';

/**
 * Detail page for a single NonConformance (NCR) report
 */
export default function NonConformanceDetail() {
  const { id } = useParams();

  const user = useUserState();

  const {
    instance: ncr,
    instanceQuery,
    refreshInstance
  } = useInstance({
    endpoint: ApiEndpoints.ncr_list,
    pk: id,
    params: {
      part_detail: true,
      tags: true
    }
  });

  const ncrStatus = useStatusCodes({ modelType: ModelType.nonconformance });

  const ncrOpen = useMemo(() => {
    return (
      ncr.status == ncrStatus.PENDING || ncr.status == ncrStatus.IN_PROGRESS
    );
  }, [ncr, ncrStatus]);

  const ncrPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'detail',
        label: t`NCR Details`,
        icon: <IconInfoCircle />,
        content: (
          <NonConformanceDetailsPanel
            instance={ncr}
            allowImageEdit
            refreshInstance={refreshInstance}
          />
        )
      },
      {
        name: 'stock-items',
        label: t`Stock Items`,
        icon: <IconList />,
        content: (
          <NonConformanceStockItemTable ncrId={ncr.pk} partId={ncr.part} />
        )
      },
      ParametersPanel({
        model_type: ModelType.nonconformance,
        model_id: ncr.pk
      }),
      AttachmentPanel({
        model_type: ModelType.nonconformance,
        model_id: ncr.pk
      }),
      NotesPanel({
        model_type: ModelType.nonconformance,
        model_id: ncr.pk,
        has_note: !!ncr.notes
      })
    ];
  }, [ncr, id, user]);

  const ncrBadges: ReactNode[] = useMemo(() => {
    if (instanceQuery.isLoading) {
      return [];
    }

    const badges: ReactNode[] = [
      <StatusRenderer
        status={ncr.status_custom_key || ncr.status}
        type={ModelType.nonconformance}
        options={{ size: 'lg' }}
      />
    ];

    return badges;
  }, [ncr, instanceQuery]);

  const ncrFields = useNonConformanceFields();

  const editNcr = useEditApiFormModal({
    url: ApiEndpoints.ncr_list,
    pk: ncr.pk,
    title: t`Edit Non-Conformance Report`,
    fields: ncrFields,
    onFormSuccess: refreshInstance
  });

  const investigateNcr = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.ncr_investigate, ncr.pk),
    title: t`Investigate NCR`,
    onFormSuccess: refreshInstance,
    preFormWarning: t`Move this NCR into investigation`,
    successMessage: t`NCR is now under investigation`
  });

  const completeNcr = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.ncr_complete, ncr.pk),
    title: t`Complete NCR`,
    onFormSuccess: refreshInstance,
    preFormContent: (
      <Alert
        color='green'
        icon={<IconCircleCheck />}
        title={t`Mark this NCR as complete`}
      />
    ),
    successMessage: t`NCR completed`
  });

  const cancelNcr = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.ncr_cancel, ncr.pk),
    title: t`Cancel NCR`,
    onFormSuccess: refreshInstance,
    preFormWarning: t`Cancel this NCR`,
    successMessage: t`NCR cancelled`
  });

  const ncrActions = useMemo(() => {
    const canEdit: boolean = user.hasChangeRole(UserRoles.ncr);

    const canInvestigate: boolean = canEdit && ncr.status == ncrStatus.PENDING;

    const canComplete: boolean = canEdit && ncrOpen;

    const canCancel: boolean = canEdit && ncrOpen;

    return [
      <PrimaryActionButton
        title={t`Investigate`}
        icon='issue'
        hidden={!canInvestigate}
        color='blue'
        onClick={() => investigateNcr.open()}
      />,
      <PrimaryActionButton
        title={t`Complete`}
        icon='complete'
        hidden={!canComplete}
        color='green'
        onClick={() => completeNcr.open()}
      />,
      <AdminButton model={ModelType.nonconformance} id={ncr.pk} />,
      <BarcodeActionDropdown
        model={ModelType.nonconformance}
        pk={ncr.pk}
        hash={ncr?.barcode_hash}
      />,
      <PrintingActions
        modelType={ModelType.nonconformance}
        items={[ncr.pk]}
        enableReports
      />,
      <OptionsActionDropdown
        tooltip={t`NCR Actions`}
        actions={[
          EditItemAction({
            hidden: !canEdit,
            tooltip: t`Edit NCR`,
            onClick: () => editNcr.open()
          }),
          CancelItemAction({
            tooltip: t`Cancel NCR`,
            hidden: !canCancel,
            onClick: () => cancelNcr.open()
          })
        ]}
      />
    ];
  }, [user, ncr, ncrOpen, ncrStatus]);

  return (
    <>
      {editNcr.modal}
      {investigateNcr.modal}
      {completeNcr.modal}
      {cancelNcr.modal}
      <InstanceDetail query={instanceQuery} requiredRole={UserRoles.ncr}>
        <Stack gap='xs'>
          <PageDetail
            title={`${t`NCR`}: ${ncr.reference}`}
            subtitle={ncr.title}
            imageUrl={ncr.part_detail?.thumbnail || ncr.part_detail?.image}
            badges={ncrBadges}
            actions={ncrActions}
            breadcrumbs={[{ name: t`Manufacturing`, url: '/manufacturing/' }]}
            lastCrumb={[
              { name: ncr.reference, url: `/manufacturing/ncr/${ncr.pk}` }
            ]}
            editAction={editNcr.open}
            editEnabled={user.hasChangePermission(ModelType.nonconformance)}
          />
          <PanelGroup
            pageKey='nonconformance'
            panels={ncrPanels}
            model={ModelType.nonconformance}
            reloadInstance={instanceQuery.refetch}
            instance={ncr}
            id={ncr.pk}
          />
        </Stack>
      </InstanceDetail>
    </>
  );
}
