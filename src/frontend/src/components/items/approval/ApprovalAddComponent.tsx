import { Trans, t } from '@lingui/macro';
import { Button, Group, TextInput, Title } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconCheck } from '@tabler/icons-react';
import { useState } from 'react';

import { api } from '../../../App';
import { ApiPaths, url } from '../../../states/ApiState';

export function ApprovalAddComponent({
  approvalPK,
  refetch
}: {
  approvalPK: string;
  refetch: () => void;
}) {
  const [commentValue, setCommentValue] = useState('');

  function addApproval(decision: boolean) {
    api
      .post(url(ApiPaths.approval_decision, approvalPK), {
        approval: approvalPK,
        decision: decision,
        comment: commentValue
      })
      .then((res) => {
        notifications.show({
          title: t`Approval added`,
          message: t`You successfully approved this order`,
          color: 'green',
          icon: <IconCheck size="1rem" />
        });
        refetch();
      })
      .catch((err) => {
        if (err.response.status === 400) {
          notifications.show({
            title: t`Approval failed`,
            message: err.response.data.non_field_errors || t`Unknown error`,
            color: 'red',
            icon: <IconCheck size="1rem" />
          });
        } else {
          console.log(err.response);
        }
      });
  }

  return (
    <>
      <Title order={6}>
        <Trans>Add approval</Trans>
      </Title>
      <TextInput
        placeholder={t`Comment`}
        label={t`Comment`}
        value={commentValue}
        onChange={(event) => setCommentValue(event.currentTarget.value)}
      />
      <Group grow spacing="xs">
        <Button
          variant="outline"
          color="green"
          onClick={() => addApproval(true)}
        >
          <Trans>Approve</Trans>
        </Button>
        <Button
          variant="outline"
          color="red"
          onClick={() => addApproval(false)}
        >
          <Trans>Reject</Trans>
        </Button>
      </Group>
    </>
  );
}
