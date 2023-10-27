import { t } from '@lingui/macro';
import { Group, LoadingOverlay, Stack, Text } from '@mantine/core';
import {
  IconBuilding,
  IconCalendarStats,
  IconClipboardList,
  IconCopy,
  IconCurrencyDollar,
  IconDots,
  IconEdit,
  IconInfoCircle,
  IconLayersLinked,
  IconLink,
  IconList,
  IconListTree,
  IconNotes,
  IconPackages,
  IconPaperclip,
  IconQrcode,
  IconShoppingCart,
  IconStack2,
  IconTestPipe,
  IconTools,
  IconTransfer,
  IconTrash,
  IconTruckDelivery,
  IconUnlink,
  IconVersions
} from '@tabler/icons-react';
import { useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';

import { ActionDropdown } from '../../components/items/ActionDropdown';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { PartCategoryTree } from '../../components/nav/PartCategoryTree';
import { AttachmentTable } from '../../components/tables/general/AttachmentTable';
import { PartParameterTable } from '../../components/tables/part/PartParameterTable';
import { PartVariantTable } from '../../components/tables/part/PartVariantTable';
import { RelatedPartTable } from '../../components/tables/part/RelatedPartTable';
import { StockItemTable } from '../../components/tables/stock/StockItemTable';
import { NotesEditor } from '../../components/widgets/MarkdownEditor';
import { editPart } from '../../functions/forms/PartForms';
import { useInstance } from '../../hooks/UseInstance';
import { ApiPaths, apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';

/**
 * Detail view for a single Part instance
 */
export default function PartDetail() {
  const { id } = useParams();

  const user = useUserState();

  const [treeOpen, setTreeOpen] = useState(false);

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
        icon: <IconInfoCircle />
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
        icon: <IconStack2 />,
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
        name: 'scheduling',
        label: t`Scheduling`,
        icon: <IconCalendarStats />
      },
      {
        name: 'stocktake',
        label: t`Stocktake`,
        icon: <IconClipboardList />
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
        <Stack spacing="xs">
          <Text>Stock: {part.in_stock}</Text>
        </Stack>
      </Group>
    );
  }, [part, id]);

  const partActions = useMemo(() => {
    // TODO: Disable actions based on user permissions
    return [
      <ActionDropdown
        key="barcode"
        tooltip={t`Barcode Actions`}
        icon={<IconQrcode />}
        actions={[
          {
            icon: <IconQrcode />,
            name: t`View`,
            tooltip: t`View part barcode`
          },
          {
            icon: <IconLink />,
            name: t`Link Barcode`,
            tooltip: t`Link custom barcode to part`,
            disabled: part?.barcode_hash
          },
          {
            icon: <IconUnlink />,
            name: t`Unlink Barcode`,
            tooltip: t`Unlink custom barcode from part`,
            disabled: !part?.barcode_hash
          }
        ]}
      />,
      <ActionDropdown
        key="stock"
        tooltip={t`Stock Actions`}
        icon={<IconPackages />}
        actions={[
          {
            icon: <IconClipboardList color="blue" />,
            name: t`Count Stock`,
            tooltip: t`Count part stock`
          },
          {
            icon: <IconTransfer color="blue" />,
            name: t`Transfer Stock`,
            tooltip: t`Transfer part stock`
          }
        ]}
      />,
      <ActionDropdown
        key="part"
        tooltip={t`Part Actions`}
        icon={<IconDots />}
        actions={[
          {
            icon: <IconEdit color="blue" />,
            name: t`Edit`,
            tooltip: t`Edit part`,
            onClick: () => {
              part.pk &&
                editPart({
                  part_id: part.pk,
                  callback: refreshInstance
                });
            }
          },
          {
            icon: <IconCopy color="green" />,
            name: t`Duplicate`,
            tooltip: t`Duplicate part`
          },
          {
            icon: <IconTrash color="red" />,
            name: t`Delete`,
            tooltip: t`Delete part`
          }
        ]}
      />
    ];
  }, [id, part, user]);

  return (
    <>
      <Stack spacing="xs">
        <LoadingOverlay visible={instanceQuery.isFetching} />
        <PartCategoryTree
          opened={treeOpen}
          onClose={() => {
            setTreeOpen(false);
          }}
          selectedCategory={part?.category}
        />
        <PageDetail
          title={t`Part` + ': ' + part.full_name}
          subtitle={part.description}
          imageUrl={part.image}
          detail={partDetail}
          breadcrumbs={breadcrumbs}
          breadcrumbAction={() => {
            setTreeOpen(true);
          }}
          actions={partActions}
        />
        <PanelGroup pageKey="part" panels={partPanels} />
      </Stack>
    </>
  );
}
