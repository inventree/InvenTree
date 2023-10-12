import { t } from '@lingui/macro';
import { Alert, Button, LoadingOverlay, Stack, Text } from '@mantine/core';
import {
  IconBuilding,
  IconCurrencyDollar,
  IconInfoCircle,
  IconLayersLinked,
  IconList,
  IconListTree,
  IconNotes,
  IconPackages,
  IconPaperclip,
  IconShoppingCart,
  IconTestPipe,
  IconTools,
  IconTruckDelivery,
  IconVersions
} from '@tabler/icons-react';
import React from 'react';
import { useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { PlaceholderPanel } from '../../components/items/Placeholder';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { AttachmentTable } from '../../components/tables/AttachmentTable';
import { RelatedPartTable } from '../../components/tables/part/RelatedPartTable';
import { StockItemTable } from '../../components/tables/stock/StockItemTable';
import { NotesEditor } from '../../components/widgets/MarkdownEditor';
import { editPart } from '../../functions/forms/PartForms';
import { useInstance } from '../../hooks/UseInstance';
import { ApiPaths, apiUrl } from '../../states/ApiState';

/**
 * Detail view for a single Part instance
 */
export default function PartDetail() {
  const { id } = useParams();

  const {
    instance: part,
    refreshInstance,
    instanceQuery
  } = useInstance({
    endpoint: ApiPaths.part_list,
    pk: id,
    params: {
      path_detail: true
    }
  });

  // Part data panels (recalculate when part data changes)
  const partPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'details',
        label: t`Details`,
        icon: <IconInfoCircle size="18" />,
        content: <PlaceholderPanel />
      },
      {
        name: 'stock',
        label: t`Stock`,
        icon: <IconPackages size="18" />,
        content: partStockTab()
      },
      {
        name: 'variants',
        label: t`Variants`,
        icon: <IconVersions size="18" />,
        hidden: !part.is_template,
        content: <PlaceholderPanel />
      },
      {
        name: 'bom',
        label: t`Bill of Materials`,
        icon: <IconListTree size="18" />,
        hidden: !part.assembly,
        content: <PlaceholderPanel />
      },
      {
        name: 'builds',
        label: t`Build Orders`,
        icon: <IconTools size="18" />,
        hidden: !part.assembly && !part.component,
        content: <PlaceholderPanel />
      },
      {
        name: 'used_in',
        label: t`Used In`,
        icon: <IconList size="18" />,
        hidden: !part.component,
        content: <PlaceholderPanel />
      },
      {
        name: 'pricing',
        label: t`Pricing`,
        icon: <IconCurrencyDollar size="18" />,
        content: <PlaceholderPanel />
      },
      {
        name: 'suppliers',
        label: t`Suppliers`,
        icon: <IconBuilding size="18" />,
        hidden: !part.purchaseable,
        content: <PlaceholderPanel />
      },
      {
        name: 'purchase_orders',
        label: t`Purchase Orders`,
        icon: <IconShoppingCart size="18" />,
        content: <PlaceholderPanel />,
        hidden: !part.purchaseable
      },
      {
        name: 'sales_orders',
        label: t`Sales Orders`,
        icon: <IconTruckDelivery size="18" />,
        content: <PlaceholderPanel />,
        hidden: !part.salable
      },
      {
        name: 'test_templates',
        label: t`Test Templates`,
        icon: <IconTestPipe size="18" />,
        content: <PlaceholderPanel />,
        hidden: !part.trackable
      },
      {
        name: 'related_parts',
        label: t`Related Parts`,
        icon: <IconLayersLinked size="18" />,
        content: <RelatedPartTable partId={part.pk ?? -1} />
      },
      {
        name: 'attachments',
        label: t`Attachments`,
        icon: <IconPaperclip size="18" />,
        content: (
          <AttachmentTable
            url={ApiPaths.part_attachment_list}
            model="part"
            pk={part.pk ?? -1}
          />
        )
      },
      {
        name: 'notes',
        label: t`Notes`,
        icon: <IconNotes size="18" />,
        content: partNotesTab()
      }
    ];
  }, [part]);

  function partNotesTab(): React.ReactNode {
    // TODO: Set edit permission based on user permissions
    return (
      <NotesEditor
        url={apiUrl(ApiPaths.part_list, part.pk)}
        data={part.notes ?? ''}
        allowEdit={true}
      />
    );
  }

  function partStockTab(): React.ReactNode {
    return (
      <StockItemTable
        params={{
          part: part.pk ?? -1
        }}
      />
    );
  }

  const breadcrumbs = useMemo(
    () => [
      { name: t`Parts`, url: '/part' },
      ...(part.category_path ?? []).map((c: any) => ({
        name: c.name,
        url: `/part/category/${c.pk}`
      }))
    ],
    [part]
  );

  return (
    <>
      <Stack spacing="xs">
        <LoadingOverlay visible={instanceQuery.isFetching} />
        <PageDetail
          title={t`Part`}
          subtitle={part.full_name}
          detail={
            <Alert color="teal" title="Part detail goes here">
              <Text>TODO: Part details</Text>
            </Alert>
          }
          breadcrumbs={breadcrumbs}
          actions={[
            <Button
              variant="outline"
              color="blue"
              onClick={() =>
                part.pk &&
                editPart({
                  part_id: part.pk,
                  callback: refreshInstance
                })
              }
            >
              Edit Part
            </Button>
          ]}
        />
        <PanelGroup panels={partPanels} />
      </Stack>
    </>
  );
}
