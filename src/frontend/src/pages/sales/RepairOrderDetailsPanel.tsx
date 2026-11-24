import { t } from '@lingui/core/macro';
import { Grid, Skeleton, Stack } from '@mantine/core';

import TagsList from '@lib/components/TagsList';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';

import {
  type DetailsField,
  DetailsTable
} from '../../components/details/Details';
import { DetailsImage } from '../../components/details/DetailsImage';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import { useParameterDetailsGrid } from '../../components/details/ParameterDetailsGrid';

/**
 * Details panel for a RepairOrder instance.
 * Used on the RepairOrder detail page, and in the model preview drawer.
 */
export function RepairOrderDetailsPanel({
  instance
}: Readonly<{
  instance: any;
}>) {
  const parametersTable = useParameterDetailsGrid({
    model_type: ModelType.repairorder,
    model_id: instance?.pk
  });

  if (!instance?.pk) return <Skeleton />;

  const tl: DetailsField[] = [
    {
      type: 'text',
      name: 'reference',
      label: t`Reference`,
      copy: true
    },
    {
      type: 'link',
      name: 'part',
      icon: 'part',
      label: t`Part`,
      model: ModelType.part,
      hidden: !instance.part
    },
    {
      type: 'text',
      name: 'description',
      label: t`Description`,
      copy: true
    },
    {
      type: 'text',
      name: 'symptoms',
      label: t`Symptoms`,
      copy: true,
      hidden: !instance.symptoms
    },
    {
      type: 'status',
      name: 'status',
      label: t`Status`,
      model: ModelType.repairorder
    },
    {
      type: 'status',
      name: 'status_custom_key',
      label: t`Custom Status`,
      model: ModelType.repairorder,
      icon: 'status',
      hidden:
        !instance.status_custom_key ||
        instance.status_custom_key == instance.status
    }
  ];

  const tr: DetailsField[] = [
    {
      type: 'link',
      name: 'customer',
      icon: 'customers',
      label: t`Customer`,
      model: ModelType.company,
      hidden: !instance.customer
    }
  ];

  const bl: DetailsField[] = [
    {
      type: 'text',
      name: 'issued_by',
      label: t`Issued By`,
      icon: 'user',
      badge: 'user',
      hidden: !instance.issued_by
    },
    {
      type: 'text',
      name: 'completed_by',
      label: t`Completed By`,
      icon: 'user',
      badge: 'user',
      hidden: !instance.completed_by
    },
    {
      type: 'text',
      name: 'responsible',
      label: t`Responsible`,
      badge: 'owner',
      hidden: !instance.responsible
    },
    {
      type: 'text',
      name: 'project_code_label',
      label: t`Project Code`,
      icon: 'reference',
      copy: true,
      hidden: !instance.project_code
    },
    {
      type: 'link',
      name: 'take_from',
      icon: 'location',
      model: ModelType.stocklocation,
      model_formatter: (location: any) =>
        location?.description
          ? `${location.name} - ${location.description}`
          : location?.name,
      label: t`Source Location`,
      hidden: !instance.take_from
    }
  ];

  const br: DetailsField[] = [
    {
      type: 'date',
      name: 'creation_date',
      label: t`Created`,
      icon: 'calendar',
      copy: true,
      hidden: !instance.creation_date
    },
    {
      type: 'date',
      name: 'start_date',
      label: t`Start Date`,
      icon: 'calendar',
      copy: true,
      hidden: !instance.start_date
    },
    {
      type: 'date',
      name: 'target_date',
      label: t`Target Date`,
      icon: 'calendar',
      copy: true,
      hidden: !instance.target_date
    },
    {
      type: 'date',
      name: 'completion_date',
      label: t`Completed`,
      icon: 'calendar',
      copy: true,
      hidden: !instance.completion_date
    }
  ];

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
          <DetailsImage
            apiPath={apiUrl(ApiEndpoints.part_list, instance.part)}
            src={instance.part_detail?.image ?? instance.part_detail?.thumbnail}
            pk={instance.part}
          />
          <Grid.Col span={{ base: 12, sm: 8 }}>
            <DetailsTable fields={tl} item={instance} />
          </Grid.Col>
        </Grid>
        <TagsList tags={instance.tags} />
      </Stack>
    </ItemDetailsGrid>
  );
}
