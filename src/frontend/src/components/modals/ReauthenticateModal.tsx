import { StylishText } from '@lib/components/StylishText';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { FlowEnum } from '@lib/types/Auth';
import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import {
  Alert,
  Button,
  Divider,
  Group,
  Modal,
  PasswordInput,
  Stack
} from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import { IconCircleCheck, IconExclamationCircle } from '@tabler/icons-react';
import { type ReactNode, useCallback, useState } from 'react';
import { api } from '../../App';
import { useServerApiState } from '../../states/ServerApiState';

/**
 * Extract the required re-authentication flow from an error response
 */
export function getReauthFlow(err: any): FlowEnum | null {
  const flows: any = err.response?.data?.data?.flows ?? [];

  if (flows.find((flow: any) => flow.id == FlowEnum.MfaReauthenticate)) {
    return FlowEnum.MfaReauthenticate;
  } else if (flows.find((flow: any) => flow.id == FlowEnum.Reauthenticate)) {
    return FlowEnum.Reauthenticate;
  } else {
    // No match found
    return null;
  }
}

/**
 * Extract an error message from an allauth error response.
 *
 * The allauth flows have a particular response structure,
 * which this function handles.
 */
export function extractErrorMessage(err: any, defaultMsg: string): string {
  const backupMsg = `${defaultMsg}: ${err.status}`;

  if (err.response?.data?.errors && err.response?.data?.errors.length > 0) {
    return err.response?.data?.errors[0]?.message ?? backupMsg;
  }

  return backupMsg;
}

type ReauthInputProps = {
  label: string;
  name: string;
  description: string;
  url: string;
};

/**
 * Internal modal component for re-authentication
 */
function ReauthenticateModalComponent({
  inputProps,
  setOpen
}: {
  inputProps: ReauthInputProps;
  setOpen: (open: boolean) => void;
}) {
  const { setAuthContext } = useServerApiState.getState();

  const [value, setValue] = useState<string>('');
  const [error, setError] = useState<string>('');

  const onSubmit = useCallback(
    (value: string) => {
      api
        .post(inputProps.url, {
          [inputProps.name]: value
        })
        .then((response) => {
          setAuthContext(response.data?.data);
          showNotification({
            title: t`Reauthentication Succeeded`,
            message: t`You have been reauthenticated successfully.`,
            color: 'green',
            icon: <IconCircleCheck />
          });
          setOpen(false);
        })
        .catch((error) => {
          setError(
            extractErrorMessage(error, t`Error during reauthentication`)
          );
          showNotification({
            title: t`Reauthentication Failed`,
            message: `${t`Failed to reauthenticate`}: ${error.status}`,
            color: 'red',
            icon: <IconExclamationCircle />
          });
        });
    },
    [inputProps]
  );

  return (
    <Stack>
      <Divider />
      <Alert
        color='yellow'
        icon={<IconExclamationCircle />}
        title={t`Reauthenticate`}
      >
        {t`Reauthentication is required to continue.`}
      </Alert>
      <PasswordInput
        required
        label={inputProps.label}
        name={inputProps.name}
        description={inputProps.description}
        value={value}
        error={error}
        onChange={(event) => setValue(event.target.value)}
      />
      <Group justify='right'>
        <Button onClick={() => setOpen(false)} color='red'>
          <Trans>Cancel</Trans>
        </Button>
        <Button onClick={() => onSubmit(value)} color='green'>
          <Trans>Submit</Trans>
        </Button>
      </Group>
    </Stack>
  );
}

function ReauthenticateModal({
  inputProps,
  opened,
  setOpen
}: {
  inputProps: ReauthInputProps;
  opened: boolean;
  setOpen: (open: boolean) => void;
}) {
  return (
    <Modal
      opened={opened}
      zIndex={9999}
      size='lg'
      onClose={() => setOpen(false)}
      title={<StylishText size='lg'>{t`Reauthenticate`}</StylishText>}
    >
      <ReauthenticateModalComponent inputProps={inputProps} setOpen={setOpen} />
    </Modal>
  );
}

/**
 * Modal for re-authenticating with password
 */
export function ReauthenticatePasswordModal({
  opened,
  setOpen
}: {
  opened: boolean;
  setOpen: (open: boolean) => void;
}) {
  return (
    <ReauthenticateModal
      opened={opened}
      setOpen={setOpen}
      inputProps={{
        label: t`Password`,
        name: 'password',
        description: t`Enter your password`,
        url: apiUrl(ApiEndpoints.auth_reauthenticate)
      }}
    />
  );
}

/**
 * Modal for re-authenticating with TOTP code
 */
export function ReauthenticateTOTPModal({
  opened,
  setOpen
}: {
  opened: boolean;
  setOpen: (open: boolean) => void;
}) {
  return (
    <ReauthenticateModal
      opened={opened}
      setOpen={setOpen}
      inputProps={{
        label: t`TOTP Code`,
        name: 'code',
        description: t`Enter one of your TOTP codes`,
        url: apiUrl(ApiEndpoints.auth_mfa_reauthenticate)
      }}
    />
  );
}

/**
 * Hook providing re-authentication modals and helpers.
 *
 * Usage:
 * - Render the returned `modals` element somewhere in the component tree
 * - Call `reauthenticate(flow)` to open the matching modal directly, or
 * - Call `handleReauthError(error)` from an API error handler; it returns true
 *   (and opens the appropriate modal) if the error indicates that the server
 *   requires the user to re-authenticate before continuing.
 */
export function useReauthenticate(): {
  reauthenticate: (flow: FlowEnum) => void;
  handleReauthError: (error: any) => boolean;
  modals: ReactNode;
} {
  const [passwordOpen, setPasswordOpen] = useState<boolean>(false);
  const [totpOpen, setTotpOpen] = useState<boolean>(false);

  const reauthenticate = useCallback((flow: FlowEnum) => {
    switch (flow) {
      case FlowEnum.Reauthenticate:
        setPasswordOpen(true);
        break;
      case FlowEnum.MfaReauthenticate:
        setTotpOpen(true);
        break;
      default:
        // Un-handled reauthentication flow
        break;
    }
  }, []);

  const handleReauthError = useCallback(
    (error: any): boolean => {
      const status = error?.status ?? error?.response?.status;

      if (status !== 401) {
        return false;
      }

      const flow = getReauthFlow(error);

      if (!flow) {
        return false;
      }

      reauthenticate(flow);
      return true;
    },
    [reauthenticate]
  );

  const modals = (
    <>
      <ReauthenticatePasswordModal
        opened={passwordOpen}
        setOpen={setPasswordOpen}
      />
      <ReauthenticateTOTPModal opened={totpOpen} setOpen={setTotpOpen} />
    </>
  );

  return { reauthenticate, handleReauthError, modals };
}
