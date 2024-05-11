import { Trans, t } from '@lingui/macro';
import {
  Alert,
  Button,
  Flex,
  Modal,
  Skeleton,
  Switch,
  Text,
  TextInput,
  useMantineTheme
} from '@mantine/core';
import { useDisclosure, useInputState } from '@mantine/hooks';
import { modals } from '@mantine/modals';
import { useQuery, useSuspenseQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';

import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { UserRoles } from '../../enums/Roles';
import { InvenTreeIcon, InvenTreeIconType } from '../../functions/icons';
import { permissionDenied } from '../../functions/notifications';
import { apiUrl } from '../../states/ApiState';
import { useGlobalSettingsState } from '../../states/SettingsState';
import { useUserState } from '../../states/UserState';

type StateButtonProps = {
  status: number;
  orderPk: number;
  refresh: () => void;
  complete?: boolean;
};

type TransitionButtonProps = {
  label: string;
  title: string;
  description: string;
  color: string;
  onClick: any;
  disabled?: boolean;
  tooltip?: string;
  icon?: InvenTreeIconType;
  flipIcon?: boolean;
};

function TransitionButton(props: TransitionButtonProps) {
  const [loading, { toggle }] = useDisclosure();

  return (
    <Button
      variant="filled"
      radius="sm"
      color={props.color}
      rightIcon={
        !props.flipIcon && props.icon && <InvenTreeIcon icon={props.icon} />
      }
      leftIcon={
        props.flipIcon && props.icon && <InvenTreeIcon icon={props.icon} />
      }
      loading={loading}
      disabled={props.disabled}
      onClick={() =>
        modals.openConfirmModal({
          title: props.title,
          children: <Text>{props.description}</Text>,
          onConfirm: () => {
            toggle();
            props.onClick();
          }
        })
      }
    >
      {props.label}
    </Button>
  );
}

function RecallButton({ pk, refresh }: { pk: number; refresh: () => void }) {
  const pending = apiUrl(ApiEndpoints.purchase_order_pending, null, { id: pk });
  return (
    <TransitionButton
      color="gray"
      title={t`Recall purchase order`}
      description={t`Recall the purchase order from Approval, returning it to Pending`}
      label="Recall"
      onClick={() =>
        api
          .post(pending)
          .then(() => refresh())
          .catch(() => permissionDenied())
      }
      icon="recall"
      flipIcon
    />
  );
}

function PendingTransitions({
  status,
  pk,
  refresh
}: {
  status: any;
  pk: any;
  refresh: () => void;
}) {
  const settings = useGlobalSettingsState();

  const approvalsActive = settings.getSetting('ENABLE_PURCHASE_ORDER_APPROVAL');
  const readyStateActive = settings.getSetting(
    'ENABLE_PURCHASE_ORDER_READY_STATUS'
  );

  const color = status['PLACED'].color;
  let label = t`Issue Order`;
  let title = label;
  let description = t`By clicking confirm, the order will be marked as issued to the supplier.`;
  let endpoint = ApiEndpoints.purchase_order_issue;

  if (approvalsActive === 'True') {
    label = t`Request Approval`;
    title = label;
    description = t`Request approval of order`;
    endpoint = ApiEndpoints.purchase_order_request_approval;
  } else if (readyStateActive === 'True') {
    label = t`Ready`;
    title = t`Ready to Issue`;
    description = t`Mark order as ready for issuance`;
    endpoint = ApiEndpoints.purchase_order_ready;
  }

  return (
    <>
      <TransitionButton
        color={color}
        title={title}
        label={label}
        description={description}
        icon="request_approval"
        onClick={() =>
          api.post(apiUrl(endpoint, null, { id: pk })).then(() => refresh())
        }
      />
    </>
  );
}

function RejectReason({ setReason }: { setReason: any }) {
  const [value, setValue] = useInputState('');

  useEffect(() => {
    setReason(value);
  }, [value]);

  return (
    <TextInput
      label={t`Order Reject Reason`}
      description={t`Reason for rejecting this Purchase Order`}
      placeholder={t`Reason (Optional)`}
      radius="sm"
      value={value}
      onChange={setValue}
    />
  );
}

function rejectModal(endpoint: any, pk: number, refresh: () => void) {
  const [value, setValue] = useState('');
  const [opened, { open, close }] = useDisclosure(false);

  const modal = (
    <Modal opened={opened} onClose={close} title="Reject Purchase Order">
      <RejectReason setReason={setValue} />
      <Flex gap="10px" justify="end" style={{ marginTop: '10px' }}>
        <Button variant="outline" color="gray" onClick={close}>
          Cancel
        </Button>
        <Button
          variant="filled"
          onClick={() => {
            close();
            api
              .post(apiUrl(endpoint, null, { id: pk }), {
                reject_reason: value
              })
              .then(() => refresh());
          }}
        >
          Submit
        </Button>
      </Flex>
    </Modal>
  );

  return {
    modal,
    open,
    close
  };
}

function ApprovalTransitions({
  pk,
  refresh
}: {
  pk: any;
  refresh: () => void;
}) {
  const settings = useGlobalSettingsState();
  const approvalsActive = settings.getSetting('ENABLE_PURCHASE_ORDER_APPROVAL');

  const approveEndpoint = ApiEndpoints.purchase_order_ready;
  const rejectEndpoint = ApiEndpoints.purchase_order_reject;

  const user = useUserState();

  if (approvalsActive !== 'True') {
    return <Button disabled>Invalid state</Button>;
  }

  const reject = rejectModal(rejectEndpoint, pk, refresh);
  const pending = apiUrl(ApiEndpoints.purchase_order_pending, null, { id: pk });

  const { data } = useSuspenseQuery({
    queryKey: ['po', 'approve', user.username(), pk],
    queryFn: async () => {
      const url = ApiEndpoints.purchase_order_approval_allowed;
      return api.get(apiUrl(url, null, { id: pk })).then((result) => {
        console.log(result);
        return result.data;
      });
    }
  });

  return (
    <>
      {data.can_approve ? (
        <Button
          variant="filled"
          radius="sm"
          color="red"
          onClick={reject.open}
          leftIcon={<InvenTreeIcon icon="reject_order" />}
        >
          Reject
        </Button>
      ) : (
        <RecallButton pk={pk} refresh={refresh} />
      )}
      <TransitionButton
        color="green"
        title={t`Approve Purchase Order`}
        description={t`Approve the Purchase order, marking it ready to issue`}
        label={t`Approve`}
        onClick={() =>
          api
            .post(apiUrl(approveEndpoint, null, { id: pk }))
            .then(() => refresh())
        }
        disabled={!data.can_approve}
        icon="approve_order"
      />
      {reject.modal}
    </>
  );
}

function ReadyTransitions({ pk, refresh }: { pk: any; refresh: () => void }) {
  const issue = apiUrl(ApiEndpoints.purchase_order_issue, null, { id: pk });
  const user = useUserState();

  const { data } = useSuspenseQuery({
    queryKey: ['po', 'issue', user.username(), pk],
    queryFn: async () => {
      const url = ApiEndpoints.purchase_order_issue_allowed;
      return api.get(apiUrl(url, null, { id: pk })).then((result) => {
        console.log('Issue', result);
        return result.data;
      });
    }
  });

  return (
    <>
      <RecallButton pk={pk} refresh={refresh} />
      <TransitionButton
        label={t`Issue Order`}
        title={t`Issue order`}
        color="primary"
        onClick={() =>
          api
            .post(issue)
            .then(() => refresh())
            .catch(() => permissionDenied())
        }
        description={t`By clicking confirm, the order will be marked as issued to the supplier.`}
        icon="issue_order"
        disabled={!data.can_issue}
      />
    </>
  );
}

function completeModal(pk: number, refresh: () => void, complete?: boolean) {
  const [opened, { open, close }] = useDisclosure(false);
  const [selected, setSelected] = useState(complete);

  const endpoint = ApiEndpoints.purchase_order_complete;

  const modal = (
    <Modal
      opened={opened}
      onClose={close}
      title={t`Complete Purchase Order`}
      size="xl"
    >
      Mark this order as complete.
      {complete ? (
        <Alert color="green">
          <Trans>All line items have been received</Trans>
        </Alert>
      ) : (
        <>
          <Alert color="yellow">
            <Trans>
              This order has line items which have not been marked as received.
              Completing this order means that the order and line items will no
              longer be editable.
            </Trans>
          </Alert>
          <Text fw={500}>
            <Trans>Accept incomplete</Trans>
          </Text>
          <Switch
            checked={selected}
            onChange={(event) => setSelected(event.currentTarget.checked)}
            label={
              <Text fs="italic">
                <Trans>
                  Allow order to be closed with incomplete line items
                </Trans>
              </Text>
            }
          />
        </>
      )}
      <Flex gap="10px" justify="end" style={{ marginTop: '10px' }}>
        <Button variant="outline" radius="sm" color="gray" onClick={close}>
          Cancel
        </Button>
        <Button
          variant="filled"
          radius="sm"
          disabled={!selected}
          onClick={() => {
            close();
            api
              .post(apiUrl(endpoint, null, { id: pk }), {
                accept_incomplete: selected
              })
              .then(() => refresh());
          }}
        >
          Submit
        </Button>
      </Flex>
    </Modal>
  );

  return {
    modal,
    open,
    close
  };
}

function CompleteTransition({
  pk,
  refresh,
  complete
}: {
  pk: number;
  refresh: () => void;
  complete?: boolean;
}) {
  const { modal, open, close } = completeModal(pk, refresh, complete);
  return (
    <>
      <Button
        variant="filled"
        color="green"
        radius="sm"
        rightIcon={<InvenTreeIcon icon="complete" />}
        onClick={open}
      >
        Complete
      </Button>
      {modal}
    </>
  );
}

export function OrderStatebuttons(props: StateButtonProps) {
  const user = useUserState();
  const hasAdd = user.hasAddRole(UserRoles.purchase_order);
  const { data } = useSuspenseQuery({
    queryKey: ['purchase_order', 'statuses'],
    queryFn: async () => {
      const url = apiUrl(ApiEndpoints.purchase_order_status);

      return api.get(url).then((response) => {
        return response.data;
      });
    }
  });

  let statusValue;

  for (const elem of Object.values<any>(data.values)) {
    if (elem.key === props.status) {
      statusValue = elem;
    }
  }

  return (
    <>
      {hasAdd && (
        <Button.Group>
          {statusValue?.key === 10 && (
            <PendingTransitions
              status={data.values}
              pk={props.orderPk}
              refresh={props.refresh}
            />
          )}
          {statusValue?.key === 20 && (
            <CompleteTransition
              pk={props.orderPk}
              refresh={props.refresh}
              complete={props.complete}
            />
          )}
          {statusValue?.key === 70 && (
            <ApprovalTransitions pk={props.orderPk} refresh={props.refresh} />
          )}
          {statusValue?.key === 80 && (
            <ReadyTransitions pk={props.orderPk} refresh={props.refresh} />
          )}
        </Button.Group>
      )}
    </>
  );
}
