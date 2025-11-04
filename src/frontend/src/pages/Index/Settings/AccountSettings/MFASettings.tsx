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
  SimpleGrid,
  Stack,
  Table,
  Tooltip
} from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import {
  IconAlertCircle,
  IconCircleCheck,
  IconExclamationCircle
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useShallow } from 'zustand/react/shallow';
import { api } from '../../../../App';
import { StylishText } from '../../../../components/items/StylishText';
import { useServerApiState } from '../../../../states/ServerApiState';
import { QrRegistrationForm } from './QrRegistrationForm';
import { parseDate } from './SecurityContent';

/**
 * Extract the required re-authentication flow from an error response
 */
function getReauthFlow(err: any): FlowEnum | null {
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
        {t`Reauthenticate to continue.`}
      </Alert>
      <PasswordInput
        required
        label={inputProps.label}
        name={inputProps.name}
        description={inputProps.description}
        value={value}
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
function ReauthenticatePasswordModal({
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
function ReauthenticateTOTPModal({
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
        name: 'TOTP',
        description: t`Enter one of your TOTP codes`,
        url: apiUrl(ApiEndpoints.auth_mfa_reauthenticate)
      }}
    />
  );
}

/**
 * Modal for registering a new TOTP token
 */
function RegisterTOTPModal({
  opened,
  setOpen,
  onReauthFlow,
  onSuccess
}: {
  opened: boolean;
  setOpen: (open: boolean) => void;
  onReauthFlow: (flow: FlowEnum) => void;
  onSuccess: () => void;
}) {
  const [url, setUrl] = useState<string>('');
  const [secret, setSecret] = useState<string>('');
  const [value, setValue] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [processing, setProcessing] = useState<boolean>(false);

  // Query to fetch TOTP registration details
  const totpQuery = useQuery({
    enabled: false,
    queryKey: ['mfa-totp-registration'],
    queryFn: async () => {
      setUrl('');
      setSecret('');

      return api
        .get(apiUrl(ApiEndpoints.auth_totp))
        .then((_response) => {
          // A successful response indicates that TOTP is already registered
          // Close the modal and show an error
          setOpen(false);
          showNotification({
            title: t`TOTP Already Registered`,
            message: t`A TOTP token is already registered for this account.`,
            color: 'green'
          });
          return {};
        })
        .catch((error) => {
          switch (error.status) {
            case 404:
              // A 404 indicates that a new TOTP registration can be started
              setUrl(error.response?.data?.meta?.totp_url ?? '');
              setSecret(error.response?.data?.meta?.secret ?? '');
              break;
            default:
              // Any other error is unexpected
              showNotification({
                title: t`Error Fetching TOTP Registration`,
                message: t`An unexpected error occurred while fetching TOTP registration data.`,
                color: 'red'
              });
              throw error;
          }

          return null;
        });
    }
  });

  // Retrieve TOTP QR code and secret from server, when modal is opened
  useEffect(() => {
    // Reset state
    setUrl('');
    setSecret('');
    setValue('');
    setError('');
    setProcessing(false);

    if (opened) {
      totpQuery.refetch();
    }
  }, [opened]);

  // Function to submit TOTP code for registration
  const submitCode = useCallback((code: string) => {
    setProcessing(true);
    setError('');

    api
      .post(apiUrl(ApiEndpoints.auth_totp), {
        code: code
      })
      .then((response) => {
        showNotification({
          title: t`TOTP Registered`,
          message: t`TOTP token registered successfully.`,
          color: 'green',
          icon: <IconCircleCheck />
        });
        setOpen(false);
        onSuccess();
      })
      .catch((error) => {
        // Set error message
        const errorMsg = `${t`Error registering TOTP token`}: ${error.status}`;

        if (error.response?.data?.errors) {
          setError(error.response?.data?.errors[0]?.message ?? errorMsg);
        } else {
          setError(errorMsg);
        }

        // A 401 error indicates that re-authentication is required
        if (error.status === 401) {
          const flow = getReauthFlow(error);
          if (flow !== null) {
            onReauthFlow(flow);
          }
        }
      })
      .finally(() => {
        setProcessing(false);
      });
  }, []);

  return (
    <Modal
      opened={opened}
      onClose={() => setOpen(false)}
      title={<StylishText size='lg'>{t`Register TOTP Token`}</StylishText>}
    >
      <Stack>
        <QrRegistrationForm
          url={url}
          secret={secret}
          value={value}
          error={error}
          setValue={setValue}
        />
        <Button
          fullWidth
          onClick={() => {
            submitCode(value);
          }}
          disabled={processing}
        >
          <Trans>Submit</Trans>
        </Button>
      </Stack>
    </Modal>
  );
}

/**
 * Section for adding new MFA methods for the user
 */
export default function MFASettings() {
  const [auth_config] = useServerApiState(
    useShallow((state) => [state.auth_config])
  );

  // Fetch list of MFA methods currently configured for the user
  const { isLoading, data, refetch } = useQuery({
    queryKey: ['mfa-list'],
    queryFn: () =>
      api
        .get(apiUrl(ApiEndpoints.auth_authenticators))
        .then((res) => res?.data?.data ?? [])
        .catch(() => [])
  });

  // Memoize the list of currently used MFA factors
  const usedFactors: string[] = useMemo(() => {
    if (isLoading || !data) return [];
    return data.map((token: any) => token.type);
  }, [isLoading, data]);

  const [reauthPassOpen, setReauthPassModalOpen] = useState<boolean>(false);
  const [reauthTOTPOpen, setReauthTOTPModalOpen] = useState<boolean>(false);
  const [registerTOTPModalOpen, setRegisterTOTPModalOpen] =
    useState<boolean>(false);

  // Callback function used to re-authenticate the user
  const reauthenticate = useCallback((flow: FlowEnum) => {
    switch (flow) {
      case FlowEnum.Reauthenticate:
        setReauthPassModalOpen(true);
        break;
      case FlowEnum.MfaReauthenticate:
        setReauthTOTPModalOpen(true);
        break;
      default:
        // Un-handled reauthentication flow
        break;
    }
  }, []);

  const registerRecoveryCodes = useCallback(() => {
    // TODO
  }, []);

  const registerWebauthn = useCallback(() => {
    // TODO
  }, []);

  const removeTOTP = useCallback(() => {
    // TODO
  }, []);

  const viewRecoveryCodes = useCallback(() => {
    // TODO
  }, []);

  const removeWebauthn = useCallback((id: number) => {
    // TODO
  }, []);

  // Memoize the list of possible MFA factors that can be registered
  const possibleFactors = useMemo(() => {
    return [
      {
        type: 'totp',
        name: t`TOTP`,
        description: t`Time-based One-Time Password`,
        function: () => setRegisterTOTPModalOpen(true),
        used: usedFactors?.includes('totp')
      },
      {
        type: 'recovery_codes',
        name: t`Recovery Codes`,
        description: t`One-Time pre-generated recovery codes`,
        function: registerRecoveryCodes,
        used: usedFactors?.includes('recovery_codes')
      },
      {
        type: 'webauthn',
        name: t`WebAuthn`,
        description: t`Web Authentication (WebAuthn) is a web standard for secure authentication`,
        function: registerWebauthn,
        used: usedFactors?.includes('webauthn')
      }
    ].filter((factor) => {
      return auth_config?.mfa?.supported_types.includes(factor.type);
    });
  }, [usedFactors, auth_config]);

  const mfaRows = useMemo(() => {
    return data.map((token: any) => (
      <Table.Tr key={`${token.created_at}-${token.type}`}>
        <Table.Td>{token.type}</Table.Td>
        <Table.Td>{parseDate(token.last_used_at)}</Table.Td>
        <Table.Td>{parseDate(token.created_at)}</Table.Td>
        <Table.Td>
          {token.type == 'totp' && (
            <Button color='red' onClick={removeTOTP}>
              <Trans>Remove</Trans>
            </Button>
          )}
          {token.type == 'recovery_codes' && (
            <Button onClick={viewRecoveryCodes}>
              <Trans>View</Trans>
            </Button>
          )}
          {token.type == 'webauthn' && (
            <Button
              color='red'
              onClick={() => {
                removeWebauthn(token.id);
              }}
            >
              <Trans>Remove</Trans>
            </Button>
          )}
        </Table.Td>
      </Table.Tr>
    ));
  }, [data]);

  return (
    <>
      <RegisterTOTPModal
        opened={registerTOTPModalOpen}
        setOpen={setRegisterTOTPModalOpen}
        onReauthFlow={reauthenticate}
        onSuccess={refetch}
      />
      <ReauthenticatePasswordModal
        opened={reauthPassOpen}
        setOpen={setReauthPassModalOpen}
      />
      <ReauthenticateTOTPModal
        opened={reauthTOTPOpen}
        setOpen={setReauthTOTPModalOpen}
      />
      <SimpleGrid cols={{ xs: 1, md: 2 }} spacing='sm'>
        {mfaRows.length > 0 ? (
          <Table stickyHeader striped highlightOnHover withTableBorder>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>
                  <Trans>Type</Trans>
                </Table.Th>
                <Table.Th>
                  <Trans>Last used at</Trans>
                </Table.Th>
                <Table.Th>
                  <Trans>Created at</Trans>
                </Table.Th>
                <Table.Th>
                  <Trans>Actions</Trans>
                </Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>{mfaRows}</Table.Tbody>
          </Table>
        ) : (
          <Alert
            title={t`Not Configured`}
            icon={<IconAlertCircle size='1rem' />}
            color='yellow'
          >
            <Trans>No multi-factor tokens configured for this account</Trans>
          </Alert>
        )}
        {possibleFactors.length > 0 ? (
          <Stack>
            <StylishText size='md'>{t`Register Authentication Method`}</StylishText>
            {possibleFactors.map((factor) => (
              <Tooltip label={factor.description} key={factor.type}>
                <Button
                  onClick={factor.function}
                  disabled={factor.used}
                  variant='outline'
                >
                  {factor.name}
                </Button>
              </Tooltip>
            ))}
          </Stack>
        ) : (
          <Alert
            title={t`No MFA Methods Available`}
            icon={<IconAlertCircle size='1rem' />}
            color='yellow'
          >
            <Trans>There are no MFA methods available for configuration</Trans>
          </Alert>
        )}
      </SimpleGrid>
    </>
  );
}
