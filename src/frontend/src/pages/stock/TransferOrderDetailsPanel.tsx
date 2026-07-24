import { ModelType } from '@lib/enums/ModelType';
import { TagsList } from '@lib/index';
import { t } from '@lingui/core/macro';
import { Grid, Skeleton, Stack } from '@mantine/core';

import {
  type DetailsField,
  DetailsTable
} from '../../components/details/Details';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import { useParameterDetailsGrid } from '../../components/details/ParameterDetailsGrid';

export function TransferOrderDetailsPanel({
  instance
}: Readonly<{
  instance: any;
}>) {
  const tl: DetailsField[] = [
    {
      type: 'text',
      name: 'reference',
      label: t`Reference`,
      copy: true
    },
    {
      type: 'link',
      name: 'take_from',
      icon: 'location',
      label: t`Source Location`,
      model: ModelType.stocklocation
    },
    {
      type: 'link',
      name: 'destination',
      icon: 'location',
      label: t`Destination Location`,
      model: ModelType.stocklocation
    },
    {
      type: 'text',
      name: 'description',
      label: t`Description`,
      copy: true
    },
    {
      type: 'status',
      name: 'status',
      label: t`Status`,
      model: ModelType.transferorder
    },
    {
      type: 'status',
      name: 'status_custom_key',
      label: t`Custom Status`,
      model: ModelType.transferorder,
      icon: 'status',
      hidden:
        !instance?.status_custom_key ||
        instance?.status_custom_key == instance?.status
    }
  ];

  const tr: DetailsField[] = [
    {
      type: 'boolean',
      name: 'consume',
      icon: 'consume',
      label: t`Consume Stock`
    },
    {
      type: 'text',
      name: 'line_items',
      label: t`Line Items`,
      icon: 'list'
    },
    {
      type: 'progressbar',
      name: 'completed',
      icon: 'progress',
      label: t`Completed Line Items`,
      total: instance?.line_items,
      progress: instance?.completed_lines
    }
  ];

  const bl: DetailsField[] = [
    {
      type: 'link',
      external: true,
      name: 'link',
      label: t`Link`,
      copy: true,
      hidden: !instance?.link
    },
    {
      type: 'text',
      name: 'project_code_label',
      label: t`Project Code`,
      icon: 'reference',
      copy: true,
      hidden: !instance?.project_code
    },
    {
      type: 'text',
      name: 'responsible',
      label: t`Responsible`,
      badge: 'owner',
      hidden: !instance?.responsible
    }
  ];

  const br: DetailsField[] = [
    {
      type: 'date',
      name: 'creation_date',
      label: t`Creation Date`,
      icon: 'calendar',
      copy: true,
      hidden: !instance?.creation_date
    },
    {
      type: 'date',
      name: 'issue_date',
      label: t`Issue Date`,
      icon: 'calendar',
      copy: true,
      hidden: !instance?.issue_date
    },
    {
      type: 'date',
      name: 'start_date',
      label: t`Start Date`,
      icon: 'calendar',
      copy: true,
      hidden: !instance?.start_date
    },
    {
      type: 'date',
      name: 'target_date',
      label: t`Target Date`,
      copy: true,
      hidden: !instance?.target_date
    },
    {
      type: 'date',
      name: 'complete_date',
      icon: 'calendar_check',
      label: t`Completion Date`,
      copy: true,
      hidden: !instance?.complete_date
    }
  ];

  const parametersTable = useParameterDetailsGrid({
    model_type: ModelType.transferorder,
    model_id: instance?.pk
  });

  if (!instance?.pk) return <Skeleton />;

  return (
    <ItemDetailsGrid
      tables={[
        { fields: tr, item: instance },
        { fields: bl, item: instance },
        { fields: br, item: instance },
        parametersTable
      ]}
    >
      <Stack gap='xs'>
        <Grid grow>
          <Grid.Col span={{ base: 12, sm: 8 }}>
            <DetailsTable fields={tl} item={instance} />
          </Grid.Col>
        </Grid>
        <TagsList tags={instance.tags} />
      </Stack>
    </ItemDetailsGrid>
  );
}
