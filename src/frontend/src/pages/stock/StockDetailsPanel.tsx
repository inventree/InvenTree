import { t } from '@lingui/core/macro';
import {
  Button,
  Grid,
  Group,
  Skeleton,
  Space,
  Stack,
  Text,
  Tooltip
} from '@mantine/core';
import { IconArrowLeft, IconArrowRight, IconSearch } from '@tabler/icons-react';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { ActionButton } from '@lib/components/ActionButton';
import TagsList from '@lib/components/TagsList';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import { getDetailUrl } from '@lib/functions/Navigation';

import {
  type DetailsField,
  DetailsTable
} from '../../components/details/Details';
import { DetailsImage } from '../../components/details/DetailsImage';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import { formatCurrency } from '../../defaults/formatters';
import { useFindSerialNumberForm } from '../../forms/StockForms';
import { useInstance } from '../../hooks/UseInstance';
import { useGlobalSettingsState } from '../../states/SettingsStates';

export function StockDetailsPanel({
  instance,
  allowImageEdit = false,
  showSerialNav = false,
  refreshInstance
}: Readonly<{
  instance: any;
  allowImageEdit?: boolean;
  showSerialNav?: boolean;
  refreshInstance?: () => void;
}>) {
  const navigate = useNavigate();
  const globalSettings = useGlobalSettingsState();

  const enableExpiry = useMemo(
    () => globalSettings.isSet('STOCK_ENABLE_EXPIRY'),
    [globalSettings]
  );

  const { instance: serialNumbers } = useInstance({
    endpoint: ApiEndpoints.stock_serial_info,
    pk: instance?.pk,
    hasPrimaryKey: true,
    disabled: !instance?.pk,
    defaultValue: {}
  });

  const { instance: fetchedPart } = useInstance({
    endpoint: ApiEndpoints.part_list,
    pk: instance?.part,
    hasPrimaryKey: true,
    disabled: !instance?.part || !!instance?.part_detail,
    defaultValue: {}
  });

  const findBySerialNumber = useFindSerialNumberForm({
    partId: instance?.part
  });

  const part = instance?.part_detail ?? fetchedPart ?? {};

  const data = useMemo(() => {
    const d = { ...instance };
    d.available_stock = Math.max(0, (d.quantity ?? 0) - (d.allocated ?? 0));
    return d;
  }, [instance]);

  const tl: DetailsField[] = [
    {
      name: 'part',
      label: t`Base Part`,
      type: 'link',
      model: ModelType.part
    },
    {
      name: 'part_detail.IPN',
      label: t`IPN`,
      type: 'text',
      copy: true,
      icon: 'part',
      hidden: !part.IPN
    },
    {
      name: 'part_detail.revision',
      label: t`Revision`,
      type: 'string',
      copy: true,
      icon: 'revision',
      hidden: !part.revision
    },
    {
      name: 'status',
      type: 'status',
      label: t`Status`,
      model: ModelType.stockitem
    },
    {
      name: 'status_custom_key',
      type: 'status',
      label: t`Custom Status`,
      model: ModelType.stockitem,
      icon: 'status',
      hidden:
        !instance?.status_custom_key ||
        instance?.status_custom_key == instance?.status
    },
    {
      type: 'link',
      name: 'link',
      label: t`Link`,
      external: true,
      copy: true,
      hidden: !instance?.link
    }
  ];

  const tr: DetailsField[] = [
    {
      type: 'text',
      name: 'serial',
      label: t`Serial Number`,
      hidden: !instance?.serial,
      ...(showSerialNav && {
        value_formatter: () => (
          <Group gap='xs' justify='space-apart'>
            <Text>{instance?.serial}</Text>
            <Space flex={10} />
            <Group gap={2} justify='right'>
              {serialNumbers?.previous?.pk && (
                <Tooltip label={t`Previous serial number`} position='top'>
                  <Button
                    p={3}
                    aria-label='previous-serial-number'
                    leftSection={<IconArrowLeft />}
                    variant='transparent'
                    size='sm'
                    onClick={() => {
                      navigate(
                        getDetailUrl(
                          ModelType.stockitem,
                          serialNumbers.previous.pk
                        )
                      );
                    }}
                  >
                    {serialNumbers.previous.serial}
                  </Button>
                </Tooltip>
              )}
              <ActionButton
                icon={<IconSearch size={18} />}
                tooltip={t`Find serial number`}
                tooltipAlignment='top'
                variant='transparent'
                onClick={findBySerialNumber.open}
              />
              {serialNumbers?.next?.pk && (
                <Tooltip label={t`Next serial number`} position='top'>
                  <Button
                    p={3}
                    aria-label='next-serial-number'
                    rightSection={<IconArrowRight />}
                    variant='transparent'
                    size='sm'
                    onClick={() => {
                      navigate(
                        getDetailUrl(ModelType.stockitem, serialNumbers.next.pk)
                      );
                    }}
                  >
                    {serialNumbers.next.serial}
                  </Button>
                </Tooltip>
              )}
            </Group>
          </Group>
        )
      })
    },
    {
      type: 'number',
      name: 'quantity',
      label: t`Quantity`,
      unit: part?.units,
      hidden: !!instance?.serial && instance?.quantity == 1
    },
    {
      type: 'number',
      name: 'available_stock',
      label: t`Available`,
      unit: part?.units,
      icon: 'stock',
      hidden: !!instance?.serial || instance.in_stock === false
    },
    {
      type: 'number',
      name: 'allocated',
      label: t`Allocated to Orders`,
      unit: part?.units,
      icon: 'tick_off',
      hidden: !instance?.allocated
    },
    {
      type: 'text',
      name: 'batch',
      label: t`Batch Code`,
      hidden: !instance?.batch
    }
  ];

  const bl: DetailsField[] = [
    {
      name: 'supplier_part',
      label: t`Supplier Part`,
      type: 'link',
      model_field: 'SKU',
      model: ModelType.supplierpart,
      hidden: !instance?.supplier_part
    },
    {
      type: 'link',
      name: 'location',
      label: t`Location`,
      model: ModelType.stocklocation,
      hidden: !instance?.location
    },
    {
      type: 'link',
      name: 'belongs_to',
      label: t`Installed In`,
      model_filters: {
        part_detail: true
      },
      model_formatter: (model: any) => {
        let text = model?.part_detail?.full_name ?? model?.name;
        if (model.serial && model.quantity == 1) {
          text += ` # ${model.serial}`;
        }
        return text;
      },
      icon: 'stock',
      model: ModelType.stockitem,
      hidden: !instance?.belongs_to
    },
    {
      type: 'link',
      name: 'parent',
      icon: 'sitemap',
      label: t`Parent Item`,
      model: ModelType.stockitem,
      hidden: !instance?.parent,
      model_formatter: () => t`Parent stock item`
    },
    {
      type: 'link',
      name: 'consumed_by',
      label: t`Consumed By`,
      model: ModelType.build,
      hidden: !instance?.consumed_by,
      icon: 'build',
      model_field: 'reference'
    },
    {
      type: 'link',
      name: 'build',
      label: t`Build Order`,
      model: ModelType.build,
      hidden: !instance?.build,
      model_field: 'reference'
    },
    {
      type: 'link',
      name: 'purchase_order',
      label: t`Purchase Order`,
      model: ModelType.purchaseorder,
      hidden: !instance?.purchase_order,
      icon: 'purchase_orders',
      model_field: 'reference'
    },
    {
      type: 'link',
      name: 'sales_order',
      label: t`Sales Order`,
      model: ModelType.salesorder,
      hidden: !instance?.sales_order,
      icon: 'sales_orders',
      model_field: 'reference'
    },
    {
      type: 'link',
      name: 'customer',
      label: t`Customer`,
      model: ModelType.company,
      hidden: !instance?.customer
    }
  ];

  const br: DetailsField[] = [
    {
      type: 'date',
      name: 'expiry_date',
      label: t`Expiry Date`,
      hidden: !enableExpiry || !instance?.expiry_date,
      icon: 'calendar'
    },
    {
      type: 'text',
      name: 'purchase_price',
      label: t`Unit Price`,
      icon: 'currency',
      hidden: !instance?.purchase_price,
      value_formatter: () =>
        formatCurrency(instance?.purchase_price, {
          currency: instance?.purchase_price_currency
        })
    },
    {
      type: 'text',
      name: 'stock_value',
      label: t`Stock Value`,
      icon: 'currency',
      hidden:
        !instance?.purchase_price ||
        instance?.quantity == 1 ||
        instance?.quantity == 0,
      value_formatter: () =>
        formatCurrency(instance?.purchase_price, {
          currency: instance?.purchase_price_currency,
          multiplier: instance?.quantity
        })
    },
    {
      type: 'text',
      name: 'packaging',
      icon: 'part',
      label: t`Packaging`,
      hidden: !instance?.packaging
    },
    {
      type: 'date',
      name: 'creation_date',
      icon: 'calendar',
      label: t`Created`,
      hidden: !instance?.creation_date
    },
    {
      type: 'date',
      name: 'updated',
      icon: 'calendar',
      label: t`Last Updated`
    },
    {
      type: 'date',
      name: 'stocktake_date',
      icon: 'calendar',
      label: t`Last Stocktake`,
      hidden: !instance?.stocktake_date
    }
  ];

  if (!instance?.pk) return <Skeleton />;

  return (
    <>
      {showSerialNav && findBySerialNumber.modal}
      <ItemDetailsGrid>
        <Stack gap='xs'>
          <Grid grow>
            <DetailsImage
              appRole={allowImageEdit ? UserRoles.part : undefined}
              imageActions={
                allowImageEdit
                  ? {
                      uploadFile: true,
                      deleteFile: true
                    }
                  : {}
              }
              apiPath={apiUrl(ApiEndpoints.part_list, instance?.part)}
              src={part?.image ?? part?.thumbnail}
              pk={instance?.part}
              refresh={refreshInstance}
            />
            <Grid.Col span={{ base: 12, sm: 8 }}>
              <DetailsTable fields={tl} item={data} />
            </Grid.Col>
          </Grid>
          <TagsList tags={instance?.tags} />
        </Stack>
        <DetailsTable fields={tr} item={data} />
        <DetailsTable fields={bl} item={data} />
        <DetailsTable fields={br} item={data} />
      </ItemDetailsGrid>
    </>
  );
}
