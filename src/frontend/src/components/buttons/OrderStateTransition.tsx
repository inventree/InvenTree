import { Trans, t } from '@lingui/macro';
import {
  Alert,
  Button,
  Flex,
  Modal,
  Switch,
  Text,
  TextInput
} from '@mantine/core';
import { useDisclosure, useInputState } from '@mantine/hooks';
import { modals } from '@mantine/modals';
import { useSuspenseQuery } from '@tanstack/react-query';
import React, { useEffect, useState } from 'react';

import { api } from '../../App';
import { colorMap } from '../../defaults/backendMappings';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { UserRoles } from '../../enums/Roles';
import { InvenTreeIcon, InvenTreeIconType } from '../../functions/icons';
import { permissionDenied } from '../../functions/notifications';
import { apiUrl } from '../../states/ApiState';
import { useGlobalSettingsState } from '../../states/SettingsState';
import { useUserState } from '../../states/UserState';

type TransitionProps = {
  orderPk: number;
  refresh: () => void;
};

type StatusObject = {
  color: string;
};

type StateButtonProps = {
  status: number | { [key: string]: StatusObject };
  complete?: boolean;
} & TransitionProps;

type TransitionButtonProps = {
  label: string;
  title: string;
  description: string;
  color: string;
  onClick: any;
  disabled?: boolean;
  icon?: InvenTreeIconType;
  flipIcon?: boolean;
};

function TransitionButton(props: Readonly<TransitionButtonProps>) {
  const [loading, { toggle }] = useDisclosure();

  return (
    <Button
      variant="filled"
      radius="sm"
      color={props.color}
      rightSection={
        !props.flipIcon && props.icon && <InvenTreeIcon icon={props.icon} />
      }
      leftSection={
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

function RecallButton(props: Readonly<TransitionProps>) {
  const pending = apiUrl(ApiEndpoints.purchase_order_recall, null, {
    id: props.orderPk
  });
  return (
    <TransitionButton
      color={colorMap.default}
      title={t`Recall purchase order`}
      description={t`Recall the purchase order from Approval, returning it to Pending`}
      label={t`Recall`}
      onClick={() =>
        api
          .post(pending)
          .then(() => props.refresh())
          .catch(() => permissionDenied())
      }
      icon="recall"
      flipIcon
    />
  );
}

function PendingTransitions(props: Readonly<StateButtonProps>) {
  const settings = useGlobalSettingsState();

  const approvalsActive = settings.getSetting('ENABLE_PURCHASE_ORDER_APPROVAL');
  const readyStateActive = settings.getSetting(
    'ENABLE_PURCHASE_ORDER_READY_STATUS'
  );

  let color =
    typeof props.status === 'object' ? props.status['PLACED'].color : 'default';
  color = colorMap[color];
  let label = t`Issue Order`;
  let title = label;
  let description = t`By clicking confirm, the order will be marked as issued to the supplier.`;
  let icon: InvenTreeIconType = 'issue_order';
  let endpoint = ApiEndpoints.purchase_order_issue;

  if (approvalsActive === 'True') {
    label = t`Request Approval`;
    title = label;
    description = t`Request approval of order`;
    icon = 'request_approval';
    endpoint = ApiEndpoints.purchase_order_request_approval;
  } else if (readyStateActive === 'True') {
    label = t`Ready`;
    title = t`Ready to Issue`;
    description = t`Mark order as ready for issuance`;
    icon = 'ready_order';
    endpoint = ApiEndpoints.purchase_order_ready;
  }

  return (
    <TransitionButton
      color={color}
      title={title}
      label={label}
      description={description}
      icon={icon}
      onClick={() =>
        api
          .post(apiUrl(endpoint, null, { id: props.orderPk }))
          .then(() => props.refresh())
      }
    />
  );
}

function RejectReason({
  setReason
}: Readonly<{ setReason: React.Dispatch<React.SetStateAction<string>> }>) {
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

type RejectModalProps = {
  endpoint: ApiEndpoints;
} & TransitionProps;

function useRejectModal(props: Readonly<RejectModalProps>) {
  const [value, setValue] = useState('');
  const [opened, { open, close }] = useDisclosure(false);

  const modal = (
    <Modal opened={opened} onClose={close} title={t`Reject Purchase Order`}>
      <RejectReason setReason={setValue} />
      <Flex gap="10px" justify="end" style={{ marginTop: '10px' }}>
        <Button variant="outline" color={colorMap.default} onClick={close}>
          <Trans>Cancel</Trans>
        </Button>
        <Button
          variant="filled"
          onClick={() => {
            close();
            api
              .post(apiUrl(props.endpoint, null, { id: props.orderPk }), {
                reject_reason: value
              })
              .then(() => props.refresh());
          }}
        >
          <Trans>Submit</Trans>
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

function ApprovalTransitions(props: Readonly<TransitionProps>) {
  const settings = useGlobalSettingsState();
  const approvalsActive = settings.getSetting('ENABLE_PURCHASE_ORDER_APPROVAL');

  const approveEndpoint = ApiEndpoints.purchase_order_ready;
  const rejectEndpoint = ApiEndpoints.purchase_order_reject;

  const user = useUserState();
  const { data } = useSuspenseQuery({
    queryKey: ['po', 'permissions', user.username(), props.orderPk],
    queryFn: async () => {
      const url = ApiEndpoints.purchase_order_state_permissions;
      return api
        .get(apiUrl(url, null, { id: props.orderPk }))
        .then((result) => {
          return result.data;
        });
    }
  });

  const reject = useRejectModal({
    endpoint: rejectEndpoint,
    ...props
  });

  if (approvalsActive !== 'True') {
    return (
      <Button disabled>
        <Trans>Invalid state</Trans>
      </Button>
    );
  }

  return (
    <>
      {data.can_approve ? (
        <Button
          variant="filled"
          radius="sm"
          color={colorMap.danger}
          onClick={reject.open}
          leftSection={<InvenTreeIcon icon="reject_order" />}
        >
          <Trans>Reject</Trans>
        </Button>
      ) : (
        <RecallButton orderPk={props.orderPk} refresh={props.refresh} />
      )}
      <TransitionButton
        color={colorMap.success}
        title={t`Approve Purchase Order`}
        description={t`Approve the Purchase order, marking it ready to issue`}
        label={t`Approve`}
        onClick={() =>
          api
            .post(apiUrl(approveEndpoint, null, { id: props.orderPk }))
            .then(() => props.refresh())
        }
        disabled={!data.can_approve}
        icon="approve_order"
      />
      {reject.modal}
    </>
  );
}

function ReadyTransitions(props: Readonly<TransitionProps>) {
  const issue = apiUrl(ApiEndpoints.purchase_order_issue, null, {
    id: props.orderPk
  });
  const user = useUserState();

  const { data } = useSuspenseQuery({
    queryKey: ['po', 'permissions', user.username(), props.orderPk],
    queryFn: async () => {
      const url = ApiEndpoints.purchase_order_state_permissions;
      return api
        .get(apiUrl(url, null, { id: props.orderPk }))
        .then((result) => {
          return result.data;
        });
    }
  });

  return (
    <>
      <RecallButton orderPk={props.orderPk} refresh={props.refresh} />
      <TransitionButton
        label={t`Issue Order`}
        title={t`Issue order`}
        color={colorMap['primary']}
        onClick={() =>
          api
            .post(issue)
            .then(() => props.refresh())
            .catch(() => permissionDenied())
        }
        description={t`By clicking confirm, the order will be marked as issued to the supplier.`}
        icon="issue_order"
        disabled={!data.can_issue}
      />
    </>
  );
}

function useCompleteModal(props: Readonly<Omit<StateButtonProps, 'status'>>) {
  const [opened, { open, close }] = useDisclosure(false);
  const [selected, setSelected] = useState(props.complete);

  const endpoint = ApiEndpoints.purchase_order_complete;

  const modal = (
    <Modal
      opened={opened}
      onClose={close}
      title={t`Complete Purchase Order`}
      size="xl"
    >
      <Trans>Mark this order as complete.</Trans>
      {props.complete ? (
        <Alert color={colorMap['success']}>
          <Trans>All line items have been received</Trans>
        </Alert>
      ) : (
        <>
          <Alert color={colorMap['warning']}>
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
        <Button
          variant="outline"
          radius="sm"
          color={colorMap.default}
          onClick={close}
        >
          <Trans>Cancel</Trans>
        </Button>
        <Button
          variant="filled"
          radius="sm"
          disabled={!selected}
          onClick={() => {
            close();
            api
              .post(apiUrl(endpoint, null, { id: props.orderPk }), {
                accept_incomplete: selected
              })
              .then(() => props.refresh());
          }}
        >
          <Trans>Submit</Trans>
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

function CompleteTransition(props: Readonly<Omit<StateButtonProps, 'status'>>) {
  const { modal, open } = useCompleteModal(props);
  return (
    <>
      <Button
        variant="filled"
        color={colorMap.success}
        radius="sm"
        rightSection={<InvenTreeIcon icon="complete" />}
        onClick={open}
      >
        <Trans>Complete</Trans>
      </Button>
      {modal}
    </>
  );
}

export function OrderStatebuttons(props: Readonly<StateButtonProps>) {
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
              orderPk={props.orderPk}
              refresh={props.refresh}
            />
          )}
          {statusValue?.key === 20 && (
            <CompleteTransition
              orderPk={props.orderPk}
              refresh={props.refresh}
              complete={props.complete}
            />
          )}
          {statusValue?.key === 70 && (
            <ApprovalTransitions
              orderPk={props.orderPk}
              refresh={props.refresh}
            />
          )}
          {statusValue?.key === 80 && (
            <ReadyTransitions orderPk={props.orderPk} refresh={props.refresh} />
          )}
        </Button.Group>
      )}
    </>
  );
}
