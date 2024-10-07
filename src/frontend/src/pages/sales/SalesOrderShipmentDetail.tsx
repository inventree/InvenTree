import { t } from '@lingui/macro';
import { Skeleton, Stack } from '@mantine/core';
import {
  IconInfoCircle,
  IconPackages,
  IconPaperclip
} from '@tabler/icons-react';
import { useMemo } from 'react';
import { useParams } from 'react-router-dom';

import AttachmentPanel from '../../components/nav/AttachmentPanel';
import InstanceDetail from '../../components/nav/InstanceDetail';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelType } from '../../components/nav/Panel';
import { PanelGroup } from '../../components/nav/PanelGroup';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { getDetailUrl } from '../../functions/urls';
import { useInstance } from '../../hooks/UseInstance';
import { useUserState } from '../../states/UserState';

export default function SalesOrderShipmentDetail() {
  const { id } = useParams();
  const user = useUserState();

  const {
    instance: shipment,
    instanceQuery,
    refreshInstance,
    requestStatus
  } = useInstance({
    endpoint: ApiEndpoints.sales_order_shipment_list,
    pk: id,
    params: {
      order_detail: true
    }
  });

  const shipmentPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'detail',
        label: t`Shipment Details`,
        icon: <IconInfoCircle />,
        content: <Skeleton />
      },
      {
        name: 'items',
        label: t`Items`,
        icon: <IconPackages />,
        content: <Skeleton />
      },
      AttachmentPanel({
        model_type: ModelType.salesordershipment,
        model_id: shipment.pk
      })
    ];
  }, [shipment]);

  return (
    <>
      <InstanceDetail status={requestStatus} loading={instanceQuery.isFetching}>
        <Stack gap="xs">
          <PageDetail
            title={t`Sales Order Shipment` + `: ${shipment.reference}`}
            breadcrumbs={[
              { name: t`Sales`, url: '/sales/' },
              {
                name: shipment.order_detail?.reference,
                url: getDetailUrl(ModelType.salesorder, shipment.order)
              }
            ]}
            editAction={() => {
              // TODO - Implement this
              // TODO - Reference SalesOrder page
            }}
            editEnabled={user.hasChangePermission(ModelType.salesordershipment)}
          />
          <PanelGroup
            pageKey="salesordershipment"
            panels={shipmentPanels}
            model={ModelType.salesordershipment}
            instance={shipment}
            id={shipment.pk}
          />
        </Stack>
      </InstanceDetail>
    </>
  );
}
