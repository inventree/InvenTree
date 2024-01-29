import { t } from '@lingui/macro';
import { LoadingOverlay, Skeleton, Stack } from '@mantine/core';
import {
  IconBuildingWarehouse,
  IconInfoCircle,
  IconList,
  IconPaperclip
} from '@tabler/icons-react';
import { useMemo } from 'react';
import { useParams } from 'react-router-dom';

import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { AttachmentTable } from '../../components/tables/general/AttachmentTable';
import ManufacturerPartParameterTable from '../../components/tables/purchasing/ManufacturerPartParameterTable';
import { SupplierPartTable } from '../../components/tables/purchasing/SupplierPartTable';
import { ApiPaths } from '../../enums/ApiEndpoints';
import { useInstance } from '../../hooks/UseInstance';

export default function ManufacturerPartDetail() {
  const { id } = useParams();

  const { instance: manufacturerPart, instanceQuery } = useInstance({
    endpoint: ApiPaths.manufacturer_part_list,
    pk: id,
    hasPrimaryKey: true,
    params: {
      part_detail: true,
      manufacturer_detail: true
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
        name: 'parameters',
        label: t`Parameters`,
        icon: <IconList />,
        content: manufacturerPart?.pk ? (
          <ManufacturerPartParameterTable
            params={{ manufacturer_part: manufacturerPart.pk }}
          />
        ) : (
          <Skeleton />
        )
      },
      {
        name: 'suppliers',
        label: t`Suppliers`,
        icon: <IconBuildingWarehouse />,
        content: manufacturerPart?.pk ? (
          <SupplierPartTable
            params={{
              manufacturer_part: manufacturerPart.pk
            }}
          />
        ) : (
          <Skeleton />
        )
      },
      {
        name: 'attachments',
        label: t`Attachments`,
        icon: <IconPaperclip />,
        content: (
          <AttachmentTable
            endpoint={ApiPaths.manufacturer_part_attachment_list}
            model="manufacturer_part"
            pk={manufacturerPart?.pk}
          />
        )
      }
    ];
  }, [manufacturerPart]);

  const breadcrumbs = useMemo(() => {
    return [
      {
        name: t`Purchasing`,
        url: '/purchasing/'
      },
      {
        name: manufacturerPart?.manufacturer_detail?.name ?? t`Manufacturer`,
        url: `/purchasing/manufacturer/${manufacturerPart?.manufacturer_detail?.pk}/`
      }
    ];
  }, [manufacturerPart]);

  return (
    <Stack spacing="xs">
      <LoadingOverlay visible={instanceQuery.isFetching} />
      <PageDetail
        title={t`ManufacturerPart`}
        subtitle={`${manufacturerPart.MPN} - ${manufacturerPart.part_detail?.name}`}
        breadcrumbs={breadcrumbs}
        imageUrl={manufacturerPart?.part_detail?.thumbnail}
      />
      <PanelGroup pageKey="manufacturerpart" panels={panels} />
    </Stack>
  );
}
