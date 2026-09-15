import { t } from '@lingui/core/macro';
import { Grid, Skeleton, Stack, Text } from '@mantine/core';
import { useMemo } from 'react';

import TagsList from '@lib/components/TagsList';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';

import {
  type DetailsField,
  DetailsTable
} from '../../components/details/Details';
import { DetailsImage } from '../../components/details/DetailsImage';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import { LineItemOverviewTable } from '../../components/details/LineItemOverviewTable';
import { useParameterDetailsGrid } from '../../components/details/ParameterDetailsGrid';
import { RenderAddress } from '../../components/render/Company';
import { formatCurrency } from '../../defaults/formatters';
import { useGlobalSettingsState } from '../../states/SettingsStates';

export function ReturnOrderDetailsPanel({
  instance,
  allowImageEdit = false,
  refreshInstance
}: Readonly<{
  instance: any;
  allowImageEdit?: boolean;
  refreshInstance?: () => void;
}>) {
  const globalSettings = useGlobalSettingsState();

  const orderCurrency = useMemo(
    () =>
      instance?.order_currency ||
      instance?.customer_detail?.currency ||
      globalSettings.getSetting('INVENTREE_DEFAULT_CURRENCY'),
    [instance, globalSettings]
  );

  const tl: DetailsField[] = [
    {
      type: 'text',
      name: 'reference',
      label: t`Reference`,
      copy: true
    },
    {
      type: 'text',
      name: 'customer_reference',
      label: t`Customer Reference`,
      icon: 'customer',
      copy: true,
      hidden: !instance?.customer_reference
    },
    {
      type: 'link',
      name: 'customer',
      icon: 'customers',
      label: t`Customer`,
      model: ModelType.company
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
      model: ModelType.returnorder
    },
    {
      type: 'status',
      name: 'status_custom_key',
      label: t`Custom Status`,
      model: ModelType.returnorder,
      icon: 'status',
      hidden:
        !instance?.status_custom_key ||
        instance?.status_custom_key == instance?.status
    }
  ];

  const tr: DetailsField[] = [
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
    },
    {
      type: 'text',
      name: 'currency',
      label: t`Order Currency`,
      value_formatter: () =>
        instance?.order_currency ?? instance?.customer_detail?.currency
    },
    {
      type: 'text',
      name: 'total_price',
      label: t`Total Cost`,
      value_formatter: () =>
        formatCurrency(instance?.total_price, {
          currency:
            instance?.order_currency || instance?.customer_detail?.currency
        })
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
      name: 'address',
      label: t`Return Address`,
      icon: 'address',
      value_formatter: () =>
        instance?.address_detail ? (
          <RenderAddress instance={instance.address_detail} />
        ) : (
          <Text size='sm' c='red'>{t`Not specified`}</Text>
        )
    },
    {
      type: 'text',
      name: 'contact_detail.name',
      label: t`Contact`,
      icon: 'user',
      copy: true,
      hidden: !instance?.contact
    },
    {
      type: 'text',
      name: 'contact_detail.email',
      label: t`Contact Email`,
      icon: 'email',
      copy: true,
      hidden: !instance?.contact_detail?.email
    },
    {
      type: 'text',
      name: 'contact_detail.phone',
      label: t`Contact Phone`,
      icon: 'phone',
      copy: true,
      hidden: !instance?.contact_detail?.phone
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
    },
    {
      type: 'date',
      name: 'updated_at',
      label: t`Last Updated`,
      icon: 'calendar',
      copy: true,
      showTime: true,
      hidden: !instance?.updated_at
    }
  ];

  const parametersTable = useParameterDetailsGrid({
    model_type: ModelType.returnorder,
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
            appRole={allowImageEdit ? UserRoles.return_order : undefined}
            imageActions={
              allowImageEdit ? { uploadFile: true, deleteFile: true } : {}
            }
            apiPath={apiUrl(ApiEndpoints.company_list, instance?.customer)}
            src={instance?.customer_detail?.image}
            pk={instance?.customer}
            refresh={refreshInstance}
          />
          <Grid.Col span={{ base: 12, sm: 8 }}>
            <DetailsTable fields={tl} item={instance} />
          </Grid.Col>
        </Grid>
        <TagsList tags={instance?.tags} />
      </Stack>
      <LineItemOverviewTable
        title={t`Line Items`}
        endpoint={ApiEndpoints.return_order_line_list}
        params={{ order: instance?.pk, part_detail: true }}
        progressLabel={t`Received`}
        progress={(record: any) => ({
          value: record.received_date ? 1 : 0,
          maximum: 1
        })}
      />
    </ItemDetailsGrid>
  );
}
