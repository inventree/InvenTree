import { t } from '@lingui/macro';
import {
  Alert,
  Button,
  Group,
  LoadingOverlay,
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
  IconStack2,
  IconTestPipe,
  IconTools,
  IconTruckDelivery,
  IconVersions
} from '@tabler/icons-react';
import { useMemo } from 'react';
import { useParams } from 'react-router-dom';

import { ApiImage } from '../../components/images/ApiImage';
import { PlaceholderPanel } from '../../components/items/Placeholder';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { AttachmentTable } from '../../components/tables/AttachmentTable';
import { PartParameterTable } from '../../components/tables/part/PartParameterTable';
import { PartVariantTable } from '../../components/tables/part/PartVariantTable';
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
    },
    refetchOnMount: true
  });

  // Part data panels (recalculate when part data changes)
  const partPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'details',
        label: t`Details`,
        icon: <IconInfoCircle />,
        content: <PlaceholderPanel />
      },
      {
        name: 'parameters',
        label: t`Parameters`,
        icon: <IconList />,
        content: <PartParameterTable partId={id ?? -1} />
      },
      {
        name: 'stock',
        label: t`Stock`,
        icon: <IconPackages />,
        content: (
          <StockItemTable
            params={{
              part: part.pk ?? -1
            }}
          />
        )
      },
      {
        name: 'variants',
        label: t`Variants`,
        icon: <IconVersions />,
        hidden: !part.is_template,
        content: <PartVariantTable partId={String(id)} />
      },
      {
        name: 'bom',
        label: t`Bill of Materials`,
        icon: <IconListTree />,
        hidden: !part.assembly,
        content: <PlaceholderPanel />
      },
      {
        name: 'builds',
        label: t`Build Orders`,
        icon: <IconTools />,
        hidden: !part.assembly && !part.component,
        content: <PlaceholderPanel />
      },
      {
        name: 'used_in',
        label: t`Used In`,
        icon: <IconStack2 />,
        hidden: !part.component,
        content: <PlaceholderPanel />
      },
      {
        name: 'pricing',
        label: t`Pricing`,
        icon: <IconCurrencyDollar />,
        content: <PlaceholderPanel />
      },
      {
        name: 'suppliers',
        label: t`Suppliers`,
        icon: <IconBuilding />,
        hidden: !part.purchaseable,
        content: <PlaceholderPanel />
      },
      {
        name: 'purchase_orders',
        label: t`Purchase Orders`,
        icon: <IconShoppingCart />,
        content: <PlaceholderPanel />,
        hidden: !part.purchaseable
      },
      {
        name: 'sales_orders',
        label: t`Sales Orders`,
        icon: <IconTruckDelivery />,
        content: <PlaceholderPanel />,
        hidden: !part.salable
      },
      {
        name: 'test_templates',
        label: t`Test Templates`,
        icon: <IconTestPipe />,
        content: <PlaceholderPanel />,
        hidden: !part.trackable
      },
      {
        name: 'related_parts',
        label: t`Related Parts`,
        icon: <IconLayersLinked />,
        content: <RelatedPartTable partId={part.pk ?? -1} />
      },
      {
        name: 'attachments',
        label: t`Attachments`,
        icon: <IconPaperclip />,
        content: (
          <AttachmentTable
            endpoint={ApiPaths.part_attachment_list}
            model="part"
            pk={part.pk ?? -1}
          />
        )
      },
      {
        name: 'notes',
        label: t`Notes`,
        icon: <IconNotes />,
        content: (
          <NotesEditor
            url={apiUrl(ApiPaths.part_list, part.pk)}
            data={part.notes ?? ''}
            allowEdit={true}
          />
        )
      }
    ];
  }, [id, part]);

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

  const partDetail = useMemo(() => {
    return (
      <Group spacing="xs" noWrap={true}>
        <ApiImage
          src={String(part.image || '')}
          radius="sm"
          height={64}
          width={64}
        />
        <Stack spacing="xs">
          <Text size="lg" weight={500}>
            {part.full_name}
          </Text>
          <Text size="sm">{part.description}</Text>
        </Stack>
      </Group>
    );
  }, [part, id]);

  return (
    <>
      <Stack spacing="xs">
        <LoadingOverlay visible={instanceQuery.isFetching} />
        <PageDetail
          detail={partDetail}
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
        <PanelGroup pageKey="part" panels={partPanels} />
      </Stack>
    </>
  );
}
