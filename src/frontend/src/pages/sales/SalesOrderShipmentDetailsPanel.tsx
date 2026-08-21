import { t } from '@lingui/core/macro';
import { Grid, Skeleton, Stack, Text } from '@mantine/core';
import { useMemo } from 'react';

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
import { RenderAddress } from '../../components/render/Company';
import { RenderUser } from '../../components/render/User';
import { formatDate } from '../../defaults/formatters';
import { useInstance } from '../../hooks/UseInstance';

export function SalesOrderShipmentDetailsPanel({
  instance,
  refreshInstance
}: Readonly<{
  instance: any;
  refreshInstance?: () => void;
}>) {
  const { instance: customer } = useInstance({
    endpoint: ApiEndpoints.company_list,
    pk: instance?.order_detail?.customer,
    hasPrimaryKey: true
  });

  const data = useMemo(
    () => ({
      ...instance,
      customer: customer?.pk,
      customer_name: customer?.name,
      customer_reference: instance?.order_detail?.customer_reference
    }),
    [instance, customer]
  );

  const address = useMemo(
    () =>
      instance?.shipment_address_detail ||
      instance?.order_detail?.address_detail,
    [instance]
  );

  const tl: DetailsField[] = [
    {
      type: 'link',
      model: ModelType.salesorder,
      name: 'order',
      label: t`Sales Order`,
      icon: 'sales_orders',
      model_field: 'reference'
    },
    {
      type: 'link',
      name: 'customer',
      icon: 'customers',
      label: t`Customer`,
      model: ModelType.company,
      model_field: 'name',
      hidden: !data.customer
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

  const tr: DetailsField[] = [
    {
      type: 'text',
      name: 'customer_reference',
      icon: 'serial',
      label: t`Customer Reference`,
      hidden: !data.customer_reference,
      copy: true
    },
    {
      type: 'text',
      name: 'reference',
      icon: 'serial',
      label: t`Shipment Reference`,
      copy: true
    },
    {
      type: 'text',
      name: 'tracking_number',
      label: t`Tracking Number`,
      icon: 'trackable',
      value_formatter: () => instance?.tracking_number || '---',
      copy: !!instance?.tracking_number
    },
    {
      type: 'text',
      name: 'invoice_number',
      label: t`Invoice Number`,
      icon: 'serial',
      value_formatter: () => instance?.invoice_number || '---',
      copy: !!instance?.invoice_number
    }
  ];

  const bl: DetailsField[] = [
    {
      type: 'text',
      name: 'address',
      label: t`Shipping Address`,
      icon: 'address',
      value_formatter: () =>
        address ? (
          <RenderAddress instance={address} />
        ) : (
          <Text size='sm' c='red'>{t`Not specified`}</Text>
        )
    }
  ];

  const br: DetailsField[] = [
    {
      type: 'text',
      name: 'allocated_items',
      icon: 'packages',
      label: t`Allocated Items`
    },
    {
      type: 'text',
      name: 'checked_by',
      label: t`Checked By`,
      icon: 'check',
      value_formatter: () =>
        instance?.checked_by_detail ? (
          <RenderUser instance={instance.checked_by_detail} />
        ) : (
          <Text size='sm' c='red'>{t`Not checked`}</Text>
        )
    },
    {
      type: 'text',
      name: 'shipment_date',
      label: t`Shipment Date`,
      icon: 'calendar',
      value_formatter: () => formatDate(instance?.shipment_date),
      hidden: !instance?.shipment_date
    },
    {
      type: 'text',
      name: 'delivery_date',
      label: t`Delivery Date`,
      icon: 'calendar',
      value_formatter: () => formatDate(instance?.delivery_date),
      hidden: !instance?.delivery_date
    }
  ];

  const parametersTable = useParameterDetailsGrid({
    model_type: ModelType.salesordershipment,
    model_id: instance?.pk
  });

  if (!instance?.pk) return <Skeleton />;

  return (
    <ItemDetailsGrid
      tables={[
        { fields: tr, item: data },
        { fields: bl, item: data },
        { fields: br, item: data },
        parametersTable
      ]}
    >
      <Stack gap='xs'>
        <Grid grow>
          <DetailsImage
            appRole={UserRoles.sales_order}
            apiPath={apiUrl(ApiEndpoints.company_list, customer?.pk)}
            src={customer?.image}
            pk={customer?.pk}
            imageActions={{
              selectExisting: false,
              downloadImage: false,
              uploadFile: false,
              deleteFile: false
            }}
          />
          <Grid.Col span={{ base: 12, sm: 8 }}>
            <DetailsTable fields={tl} item={data} />
          </Grid.Col>
        </Grid>
        <TagsList tags={instance?.tags} />
      </Stack>
    </ItemDetailsGrid>
  );
}
