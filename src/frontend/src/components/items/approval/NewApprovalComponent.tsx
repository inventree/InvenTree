import { Trans } from '@lingui/macro';
import { t } from '@lingui/macro';
import { Button, Text } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconCheck } from '@tabler/icons-react';

import { api } from '../../../App';
import { ApiPaths, url } from '../../../states/ApiState';

function startApproval(poPK: string, refetch: () => void) {
  return api
    .post(url(ApiPaths.approval_start), {
      name: 'test',
      model: 'order.purchaseorder',
      object_id: poPK
    })
    .then((res) => {
      console.log(res.data);
      notifications.show({
        title: t`Approval started`,
        message: t`Welcome back!`,
        color: 'green',
        icon: <IconCheck size="1rem" />
      });
      refetch();
    })
    .catch((err) => {
      if (err.response.status === 400) {
        notifications.show({
          title: t`Approval start failed`,
          message: err.response.data.non_field_errors || t`Unknown error`,
          color: 'red',
          icon: <IconCheck size="1rem" />
        });
      } else {
        console.log(err.response);
      }
    });
}

export function NewApprovalComponent({
  poPK,
  refetch
}: {
  poPK: string;
  refetch: () => void;
}) {
  return (
    <>
      <Button
        w={'100%'}
        variant="outline"
        color="green"
        onClick={() => startApproval(poPK, refetch)}
      >
        <Trans>Start approval</Trans>
      </Button>
      <Text>
        <Trans>There is currently no approval for this order.</Trans>
      </Text>
    </>
  );
}
