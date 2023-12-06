import { t } from '@lingui/macro';
import { Group, LoadingOverlay, Stack, Table } from '@mantine/core';
import {
  IconClipboardCheck,
  IconClipboardList,
  IconCopy,
  IconDots,
  IconEdit,
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
import { useCallback, useMemo } from 'react';
import { useParams } from 'react-router-dom';

import {
  ActionDropdown,
  DeleteItemAction,
  DuplicateItemAction,
  EditItemAction,
  LinkBarcodeAction,
  UnlinkBarcodeAction,
  ViewBarcodeAction
} from '../../components/items/ActionDropdown';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { StatusRenderer } from '../../components/render/StatusRenderer';
import { BuildOrderTable } from '../../components/tables/build/BuildOrderTable';
import { AttachmentTable } from '../../components/tables/general/AttachmentTable';
import { StockItemTable } from '../../components/tables/stock/StockItemTable';
import { NotesEditor } from '../../components/widgets/MarkdownEditor';
import { ApiPaths } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { buildOrderFields } from '../../forms/BuildForms';
import { openEditApiForm } from '../../functions/forms';
import { useInstance } from '../../hooks/UseInstance';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';

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
    endpoint: ApiPaths.build_order_list,
    pk: id,
    params: {
      part_detail: true
    },
    refetchOnMount: true
  });

  const buildDetailsPanel = useMemo(() => {
    return (
      <Group position="apart" grow>
        <Table striped>
          <tbody>
            <tr>
              <td>{t`Base Part`}</td>
              <td>{build.part_detail?.name}</td>
            </tr>
            <tr>
              <td>{t`Quantity`}</td>
              <td>{build.quantity}</td>
            </tr>
            <tr>
              <td>{t`Build Status`}</td>
              <td>
                {build.status && (
                  <StatusRenderer
                    status={build.status}
                    type={ModelType.build}
                  />
                )}
              </td>
            </tr>
          </tbody>
        </Table>
        <Table></Table>
      </Group>
    );
  }, [build]);

  const buildPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'details',
        label: t`Build Details`,
        icon: <IconInfoCircle />,
        content: buildDetailsPanel
      },
      {
        name: 'allocate-stock',
        label: t`Allocate Stock`,
        icon: <IconListCheck />
        // TODO: Hide if build is complete
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
              build: id ?? -1,
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
              consumed_by: id ?? -1
            }}
          />
        )
      },
      {
        name: 'child-orders',
        label: t`Child Build Orders`,
        icon: <IconSitemap />,
        content: (
          <BuildOrderTable
            params={{
              parent: id ?? -1
            }}
          />
        )
      },
      {
        name: 'attachments',
        label: t`Attachments`,
        icon: <IconPaperclip />,
        content: (
          <AttachmentTable
            endpoint={ApiPaths.build_order_attachment_list}
            model="build"
            pk={Number(id ?? -1)}
          />
        )
      },
      {
        name: 'notes',
        label: t`Notes`,
        icon: <IconNotes />,
        content: (
          <NotesEditor
            url={apiUrl(ApiPaths.build_order_list, build.pk)}
            data={build.notes ?? ''}
            allowEdit={true}
          />
        )
      }
    ];
  }, [build, id]);

  const editBuildOrder = useCallback(() => {
    let fields = buildOrderFields();

    // Cannot edit part field after creation
    fields['part'].hidden = true;

    build.pk &&
      openEditApiForm({
        url: ApiPaths.build_order_list,
        pk: build.pk,
        title: t`Edit Build Order`,
        fields: fields,
        successMessage: t`Build Order updated`,
        onFormSuccess: () => {
          refreshInstance();
        }
      });
  }, [build]);

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
            onClick: editBuildOrder
          }),
          DuplicateItemAction({}),
          DeleteItemAction({})
        ]}
      />
    ];
  }, [id, build, user]);

  const buildDetail = useMemo(() => {
    return StatusRenderer({
      status: build.status,
      type: ModelType.build
    });
  }, [build, id]);

  return (
    <>
      <Stack spacing="xs">
        <LoadingOverlay visible={instanceQuery.isFetching} />
        <PageDetail
          title={build.reference}
          subtitle={build.title}
          detail={buildDetail}
          imageUrl={build.part_detail?.thumbnail}
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
