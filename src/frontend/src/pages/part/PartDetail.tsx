import { t } from '@lingui/macro';
import {
  Button,
  Group,
  LoadingOverlay,
  Space,
  Stack,
  Text
} from '@mantine/core';
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
import { useQuery } from '@tanstack/react-query';
import React, { useState } from 'react';
import { useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { api } from '../../App';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { AttachmentTable } from '../../components/tables/AttachmentTable';
import { RelatedPartTable } from '../../components/tables/part/RelatedPartTable';
import { StockItemTable } from '../../components/tables/stock/StockItemTable';
import {
  MarkdownEditor,
  NotesEditor
} from '../../components/widgets/MarkdownEditor';
import { editPart } from '../../functions/forms/PartForms';

export default function PartDetail() {
  const { id } = useParams();

  // Part data
  const [part, setPart] = useState<any>({});

  // Part data panels (recalculate when part data changes)
  const partPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'details',
        label: t`Details`,
        icon: <IconInfoCircle size="18" />,
        content: <Text>part details go here</Text>
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
        content: <Text>part variants go here</Text>
      },
      {
        name: 'bom',
        label: t`Bill of Materials`,
        icon: <IconListTree size="18" />,
        hidden: !part.assembly,
        content: part.assembly && <Text>part BOM goes here</Text>
      },
      {
        name: 'builds',
        label: t`Build Orders`,
        icon: <IconTools size="18" />,
        hidden: !part.assembly && !part.component,
        content: <Text>part builds go here</Text>
      },
      {
        name: 'used_in',
        label: t`Used In`,
        icon: <IconList size="18" />,
        hidden: !part.component,
        content: <Text>part used in goes here</Text>
      },
      {
        name: 'pricing',
        label: t`Pricing`,
        icon: <IconCurrencyDollar size="18" />,
        content: <Text>part pricing goes here</Text>
      },
      {
        name: 'suppliers',
        label: t`Suppliers`,
        icon: <IconBuilding size="18" />,
        content: <Text>part suppliers go here</Text>,
        hidden: !part.purchaseable
      },
      {
        name: 'purchase_orders',
        label: t`Purchase Orders`,
        icon: <IconShoppingCart size="18" />,
        content: <Text>part purchase orders go here</Text>,
        hidden: !part.purchaseable
      },
      {
        name: 'sales_orders',
        label: t`Sales Orders`,
        icon: <IconTruckDelivery size="18" />,
        content: <Text>part sales orders go here</Text>,
        hidden: !part.salable
      },
      {
        name: 'test_templates',
        label: t`Test Templates`,
        icon: <IconTestPipe size="18" />,
        content: <Text>part test templates go here</Text>,
        hidden: !part.trackable
      },
      {
        name: 'related_parts',
        label: t`Related Parts`,
        icon: <IconLayersLinked size="18" />,
        content: partRelatedTab()
      },
      {
        name: 'attachments',
        label: t`Attachments`,
        icon: <IconPaperclip size="18" />,
        content: partAttachmentsTab()
      },
      {
        name: 'notes',
        label: t`Notes`,
        icon: <IconNotes size="18" />,
        content: partNotesTab()
      }
    ];
  }, [part]);

  // Query hook for fetching part data
  const partQuery = useQuery(['part', id], async () => {
    let url = `/part/${id}/`;

    return api
      .get(url)
      .then((response) => {
        setPart(response.data);
        return response.data;
      })
      .catch((error) => {
        setPart({});
        return null;
      });
  });

  function partAttachmentsTab(): React.ReactNode {
    return (
      <AttachmentTable
        url="/part/attachment/"
        model="part"
        pk={part.pk ?? -1}
      />
    );
  }

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
  return (
    <>
      <Stack spacing="xs">
        <LoadingOverlay visible={partQuery.isFetching} />
        <Group position="apart">
          <Group position="left">
            <Text size="lg">Part Detail</Text>
            <Text>{part.name}</Text>
            <Text size="sm">{part.description}</Text>
          </Group>
          <Space />
          <Text>In Stock: {part.total_in_stock}</Text>
          <Button
            variant="outline"
            color="blue"
            onClick={() =>
              part.pk &&
              editPart({
                part_id: part.pk,
                callback: () => {
                  partQuery.refetch();
                }
              })
            }
          >
            Edit Part
          </Button>
        </Group>
        <PanelGroup panels={partPanels} />
      </Stack>
    </>
  );
}
