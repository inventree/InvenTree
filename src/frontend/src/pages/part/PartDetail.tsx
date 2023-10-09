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
    url: '/part/',
    pk: id,
    params: { path_detail: true }
  });

  // Part data panels (recalculate when part data changes)
  const partPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'details',
        label: t`Details`,
        icon: <IconInfoCircle />
      },
      {
        name: 'stock',
        label: t`Stock`,
        icon: <IconPackages />,
        content: partStockTab()
      },
      {
        name: 'variants',
        label: t`Variants`,
        icon: <IconVersions />,
        hidden: !part.is_template
      },
      {
        name: 'bom',
        label: t`Bill of Materials`,
        icon: <IconListTree />,
        hidden: !part.assembly
      },
      {
        name: 'builds',
        label: t`Build Orders`,
        icon: <IconTools />,
        hidden: !part.assembly && !part.component
      },
      {
        name: 'used_in',
        label: t`Used In`,
        icon: <IconList />,
        hidden: !part.component
      },
      {
        name: 'pricing',
        label: t`Pricing`,
        icon: <IconCurrencyDollar />
      },
      {
        name: 'suppliers',
        label: t`Suppliers`,
        icon: <IconBuilding />,
        hidden: !part.purchaseable
      },
      {
        name: 'purchase_orders',
        label: t`Purchase Orders`,
        icon: <IconShoppingCart />,
        hidden: !part.purchaseable
      },
      {
        name: 'sales_orders',
        label: t`Sales Orders`,
        icon: <IconTruckDelivery />,
        hidden: !part.salable
      },
      {
        name: 'test_templates',
        label: t`Test Templates`,
        icon: <IconTestPipe />,
        hidden: !part.trackable
      },
      {
        name: 'related_parts',
        label: t`Related Parts`,
        icon: <IconLayersLinked />,
        content: partRelatedTab()
      },
      {
        name: 'attachments',
        label: t`Attachments`,
        icon: <IconPaperclip />,
        content: (
          <AttachmentTable
            url="/part/attachment/"
            model="part"
            pk={part.pk ?? -1}
          />
        )
      },
      {
        name: 'notes',
        label: t`Notes`,
        icon: <IconNotes />,
        content: partNotesTab()
      }
    ];
  }, [part]);

  function partRelatedTab(): React.ReactNode {
    return <RelatedPartTable partId={part.pk ?? -1} />;
  }
  function partNotesTab(): React.ReactNode {
    // TODO: Set edit permission based on user permissions
    return (
      <NotesEditor
        url={`/part/${part.pk}/`}
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
