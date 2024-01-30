import { t } from '@lingui/macro';
import { LoadingOverlay, Skeleton, Stack } from '@mantine/core';
import {
  IconCurrencyDollar,
  IconInfoCircle,
  IconPackages,
  IconShoppingCart
} from '@tabler/icons-react';
import { useMemo } from 'react';
import { useParams } from 'react-router-dom';

import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { PurchaseOrderTable } from '../../components/tables/purchasing/PurchaseOrderTable';
import { ApiPaths } from '../../enums/ApiEndpoints';
import { useInstance } from '../../hooks/UseInstance';

export default function SupplierPartDetail() {
  const { id } = useParams();

  const { instance: supplierPart, instanceQuery } = useInstance({
    endpoint: ApiPaths.supplier_part_list,
    pk: id,
    hasPrimaryKey: true,
    params: {
      part_detail: true,
      supplier_detail: true
    }
  });

  const panels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'details',
        label: t`Details`,
        icon: <IconInfoCircle />
      },
      {
        name: 'stock',
        label: t`Received Stock`,
        icon: <IconPackages />
      },
      {
        name: 'purchaseorders',
        label: t`Purchase Orders`,
        icon: <IconShoppingCart />,
        content: supplierPart?.pk ? (
          <PurchaseOrderTable
            supplierPartId={{ supplier_part: supplierPart.pk }}
          />
        ) : (
          <Skeleton />
        )
      },
      {
        name: 'pricing',
        label: t`Pricing`,
        icon: <IconCurrencyDollar />
      }
    ];
  }, [supplierPart]);

  const breadcrumbs = useMemo(() => {
    return [
      {
        name: t`Purchasing`,
        url: '/purchasing/'
      },
      {
        name: supplierPart?.supplier_detail?.name ?? t`Supplier`,
        url: `/purchasing/supplier/${supplierPart?.supplier_detail?.pk ?? ''}`
      }
    ];
  }, [supplierPart]);

  return (
    <Stack spacing="xs">
      <LoadingOverlay visible={instanceQuery.isFetching} />
      <PageDetail
        title={t`Supplier Part`}
        subtitle={`${supplierPart.SKU} - ${supplierPart?.part_detail?.name}`}
        breadcrumbs={breadcrumbs}
        imageUrl={supplierPart?.part_detail?.thumbnail}
      />
      <PanelGroup pageKey="supplierpart" panels={panels} />
    </Stack>
  );
}
