import { t } from '@lingui/core/macro';
import { Grid, Skeleton, Stack } from '@mantine/core';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import { TagsList } from '@lib/index';

import {
  type DetailsField,
  DetailsTable
} from '../../components/details/Details';
import { DetailsImage } from '../../components/details/DetailsImage';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';

export function CompanyDetailsPanel({
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
      type: 'text',
      name: 'description',
      label: t`Description`,
      copy: true
    },
    {
      type: 'link',
      name: 'website',
      label: t`Website`,
      external: true,
      copy: true,
      hidden: !instance?.website
    },
    {
      type: 'text',
      name: 'phone',
      label: t`Phone Number`,
      copy: true,
      hidden: !instance?.phone
    },
    {
      type: 'text',
      name: 'email',
      label: t`Email Address`,
      copy: true,
      hidden: !instance?.email
    },
    {
      type: 'text',
      name: 'tax_id',
      label: t`Tax ID`,
      copy: true,
      hidden: !instance?.tax_id
    }
  ];

  const tr: DetailsField[] = [
    {
      type: 'string',
      name: 'currency',
      label: t`Default Currency`
    },
    {
      type: 'boolean',
      name: 'is_supplier',
      label: t`Supplier`,
      icon: 'suppliers'
    },
    {
      type: 'boolean',
      name: 'is_manufacturer',
      label: t`Manufacturer`,
      icon: 'manufacturers'
    },
    {
      type: 'boolean',
      name: 'is_customer',
      label: t`Customer`,
      icon: 'customers'
    }
  ];

  if (!instance?.pk) return <Skeleton />;

  return (
    <ItemDetailsGrid tables={[{ item: instance, fields: tr }]}>
      <Stack gap='xs'>
        <Grid grow>
          <DetailsImage
            appRole={allowImageEdit ? UserRoles.purchase_order : undefined}
            apiPath={apiUrl(ApiEndpoints.company_list, instance.pk)}
            src={instance.image}
            pk={instance.pk}
            refresh={refreshInstance}
            imageActions={
              allowImageEdit
                ? {
                    uploadFile: true,
                    downloadImage: true,
                    deleteFile: true
                  }
                : {}
            }
          />
          <Grid.Col span={{ base: 12, sm: 8 }}>
            <DetailsTable item={instance} fields={tl} />
          </Grid.Col>
        </Grid>
        <TagsList tags={instance.tags} />
      </Stack>
    </ItemDetailsGrid>
  );
}
