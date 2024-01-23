import { t } from '@lingui/macro';
import { LoadingOverlay, Stack } from '@mantine/core';
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
import { ApiPaths } from '../../enums/ApiEndpoints';
import { useInstance } from '../../hooks/UseInstance';
import { useUserState } from '../../states/UserState';

export default function ManufacturerPartDetail() {
  const { id } = useParams();
  const user = useUserState();

  const {
    instance: manufacturerPart,
    refreshInstance,
    instanceQuery
  } = useInstance({
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
        icon: <IconList />
      },
      {
        name: 'suppliers',
        label: t`Suppliers`,
        icon: <IconBuildingWarehouse />
      },
      {
        name: 'attachments',
        label: t`Attachments`,
        icon: <IconPaperclip />
      }
    ];
  }, []);

  const breadcrumbs = useMemo(() => {
    return [
      {
        name: t`Purchasing`,
        url: '/purchasing/'
      },
      {
        name: manufacturerPart?.manufacturer_detail?.name ?? t`Manufacturer`,
        url: `/company/manufacturer/${manufacturerPart?.manufacturer_detail?.id}/`
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
