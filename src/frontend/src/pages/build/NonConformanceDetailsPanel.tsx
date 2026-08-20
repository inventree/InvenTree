import { t } from '@lingui/core/macro';
import { Grid, Skeleton, Stack } from '@mantine/core';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import { TagsList } from '@lib/index';

import {
  type DetailsField,
  DetailsTable
} from '../../components/details/Details';
import { DetailsImage } from '../../components/details/DetailsImage';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import { useParameterDetailsGrid } from '../../components/details/ParameterDetailsGrid';
import { ncrDispositionStatusType } from '../../defaults/backendMappings';

function severityLabel(severity: number | undefined | null): string {
  switch (severity) {
    case 10:
      return t`Minor`;
    case 20:
      return t`Major`;
    case 30:
      return t`Critical`;
    default:
      return '-';
  }
}

export function NonConformanceDetailsPanel({
  instance,
  allowImageEdit = false,
  refreshInstance
}: Readonly<{
  instance: any;
  allowImageEdit?: boolean;
  refreshInstance?: () => void;
}>) {
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
      hidden: !instance?.part_detail?.IPN,
      copy: true
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
      label: t`Title`,
      hidden: !instance?.title,
      copy: true
    },
    {
      type: 'status',
      name: 'status',
      label: t`Status`,
      model: ModelType.nonconformance
    },
    {
      type: 'status',
      name: 'status_custom_key',
      label: t`Custom Status`,
      model: ModelType.nonconformance,
      icon: 'status',
      hidden:
        !instance?.status_custom_key ||
        instance?.status_custom_key == instance?.status
    },
    {
      type: 'status',
      name: 'disposition',
      label: t`Disposition`,
      model: ncrDispositionStatusType as ModelType
    },
    {
      type: 'text',
      name: 'severity',
      label: t`Severity`,
      hidden: !instance?.severity,
      value_formatter: () => severityLabel(instance?.severity)
    }
  ];

  const tr: DetailsField[] = [
    {
      type: 'text',
      name: 'description',
      label: t`Description`,
      copy: true
    },
    {
      type: 'number',
      name: 'quantity',
      label: t`Quantity`,
      hidden: instance?.quantity === null || instance?.quantity === undefined
    },
    {
      type: 'link',
      name: 'build_order',
      icon: 'build_order',
      label: t`Build Order`,
      model: ModelType.build,
      hidden: !instance?.build_order
    },
    {
      type: 'link',
      name: 'sales_order',
      icon: 'sales_orders',
      label: t`Sales Order`,
      model: ModelType.salesorder,
      hidden: !instance?.sales_order
    },
    {
      type: 'link',
      name: 'purchase_order',
      icon: 'purchase_orders',
      label: t`Purchase Order`,
      model: ModelType.purchaseorder,
      hidden: !instance?.purchase_order
    },
    {
      type: 'link',
      name: 'return_order',
      icon: 'return_orders',
      label: t`Return Order`,
      model: ModelType.returnorder,
      hidden: !instance?.return_order
    }
  ];

  const bl: DetailsField[] = [
    {
      type: 'text',
      name: 'responsible',
      label: t`Responsible`,
      badge: 'owner',
      hidden: !instance?.responsible
    },
    {
      type: 'text',
      name: 'raised_by',
      label: t`Raised By`,
      icon: 'user',
      badge: 'user',
      hidden: !instance?.raised_by
    },
    {
      type: 'text',
      name: 'root_cause',
      label: t`Root Cause`,
      hidden: !instance?.root_cause
    },
    {
      type: 'text',
      name: 'corrective_action',
      label: t`Corrective Action`,
      hidden: !instance?.corrective_action
    },
    {
      type: 'link',
      external: true,
      name: 'link',
      label: t`Link`,
      copy: true,
      hidden: !instance?.link
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
      name: 'target_date',
      label: t`Target Date`,
      icon: 'calendar',
      copy: true,
      hidden: !instance?.target_date
    },
    {
      type: 'date',
      name: 'closed_date',
      label: t`Closed Date`,
      icon: 'calendar_check',
      copy: true,
      hidden: !instance?.closed_date
    }
  ];

  const parametersTable = useParameterDetailsGrid({
    model_type: ModelType.nonconformance,
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
          <DetailsImage
            appRole={allowImageEdit ? UserRoles.part : undefined}
            apiPath={apiUrl(ApiEndpoints.part_list, instance?.part)}
            src={
              instance?.part_detail?.image ?? instance?.part_detail?.thumbnail
            }
            pk={instance?.part}
            refresh={refreshInstance}
          />
          <Grid.Col span={{ base: 12, sm: 8 }}>
            <DetailsTable fields={tl} item={instance} />
          </Grid.Col>
        </Grid>
        <TagsList tags={instance?.tags} />
      </Stack>
    </ItemDetailsGrid>
  );
}
