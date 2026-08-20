import { create } from '@github/webauthn-json/browser-ponyfill';
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
  Loader,
  Modal,
  Paper,
  PasswordInput,
  SimpleGrid,
  Stack,
  Table,
  Text,
  Tooltip
} from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import {
  IconAlertCircle,
  IconCircleCheck,
  IconExclamationCircle,
  IconInfoCircle
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useShallow } from 'zustand/react/shallow';
import { api, queryClient } from '../../../../App';
import { CopyButton } from '../../../../components/buttons/CopyButton';
import { StylishText } from '../../../../components/items/StylishText';
import { authApi, doLogout } from '../../../../functions/auth';
import { useServerApiState } from '../../../../states/ServerApiState';
import { useGlobalSettingsState } from '../../../../states/SettingsStates';
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

/**
 * Extract an error message from an allauth error response.
 *
 * The allauth flows have a particular response structure,
 * which this function handles.
 */
function extractErrorMessage(err: any, defaultMsg: string): string {
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
        {t`Reauthentiction is required to continue.`}
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
        name: 'code',
        description: t`Enter one of your TOTP codes`,
        url: apiUrl(ApiEndpoints.auth_mfa_reauthenticate)
      }}
    />
  );
}

/**
 * Modal for removing a registered WebAuthn credential:
 * - Deletes the WebAuthn credential from the server
 * - Handles errors and re-authentication flows as needed
 */
function RemoveWebauthnModal({
  tokenId,
  opened,
  setOpen,
  onReauthFlow,
  onSuccess
}: {
  opened: boolean;
  tokenId: number | null;
  setOpen: (open: boolean) => void;
  onReauthFlow: (flow: FlowEnum) => void;
  onSuccess: () => void;
}) {
  const [processing, setProcessing] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    setProcessing(false);
    setError('');
  }, [opened]);

  const removeCredential = useCallback(() => {
    setProcessing(true);

    if (!tokenId) {
      return;
    }

    authApi(
      apiUrl(ApiEndpoints.auth_webauthn),
      {
        timeout: 30 * 1000
      },
      'delete',
      {
        authenticators: [tokenId]
      }
    )
      .then((response) => {
        showNotification({
          title: t`WebAuthn Credential Removed`,
          message: t`WebAuthn credential removed successfully.`,
          color: 'green',
          icon: <IconCircleCheck />
        });
        setOpen(false);
        onSuccess();
      })
      .catch((error) => {
        setError(
          extractErrorMessage(error, t`Error removing WebAuthn credential`)
        );

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
  }, [tokenId]);

  return (
    <Modal
      opened={opened}
      onClose={() => setOpen(false)}
      title={
        <StylishText size='lg'>{t`Remove WebAuthn Credential`}</StylishText>
      }
    >
      <Stack>
        <Divider />
        <Alert
          color='red'
          icon={<IconAlertCircle />}
          title={t`Confirm Removal`}
        >
          <Trans>Confirm removal of webauth credential</Trans>
        </Alert>
        {error && (
          <Alert color='red' icon={<IconExclamationCircle />} title={t`Error`}>
            {error}
          </Alert>
        )}
        <Group justify='right'>
          <Button onClick={() => setOpen(false)}>
            <Trans>Cancel</Trans>
          </Button>
          <Button onClick={removeCredential} color='red' disabled={processing}>
            <Trans>Remove</Trans>
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}

/**
 * Modal for removing a registered TOTP token:
 * - Deletes the TOTP token from the server
 * - Handles errors and re-authentication flows as needed
 */
function RemoveTOTPModal({
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
  const [processing, setProcessing] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    setProcessing(false);
    setError('');
  }, [opened]);

  const deleteToken = useCallback(() => {
    setProcessing(true);
    api
      .delete(apiUrl(ApiEndpoints.auth_totp), {
        timeout: 30 * 1000
      })
      .then((response) => {
        showNotification({
          title: t`TOTP Removed`,
          message: t`TOTP token removed successfully.`,
          color: 'green',
          icon: <IconCircleCheck />
        });
        setOpen(false);
        onSuccess();

        return response.data;
      })
      .catch((error) => {
        setError(extractErrorMessage(error, t`Error removing TOTP token`));

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
      title={<StylishText size='lg'>{t`Remove TOTP Token`}</StylishText>}
    >
      <Stack>
        <Divider />
        <Alert
          color='red'
          icon={<IconAlertCircle />}
          title={t`Confirm Removal`}
        >
          <Trans>Confirm removal of TOTP code</Trans>
        </Alert>
        {error && (
          <Alert color='red' icon={<IconExclamationCircle />} title={t`Error`}>
            {error}
          </Alert>
        )}
        <Group justify='right'>
          <Button onClick={() => setOpen(false)}>
            <Trans>Cancel</Trans>
          </Button>
          <Button onClick={deleteToken} color='red' disabled={processing}>
            <Trans>Remove</Trans>
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}

/**
 * Modal for registering a new TOTP token
 * - Fetches TOTP registration details from the server
 * - Displays QR code and secret to the user
 * - Accepts TOTP code input from the user
 * - Submits TOTP code to the server for registration
 * - Handles errors and re-authentication flows as needed
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
      .post(
        apiUrl(ApiEndpoints.auth_totp),
        {
          code: code
        },
        {
          timeout: 30 * 1000
        }
      )
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
        setError(extractErrorMessage(error, t`Error registering TOTP token`));

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

function RecoveryCodesModal({
  opened,
  setOpen,
  onReauthFlow
}: {
  opened: boolean;
  setOpen: (open: boolean) => void;
  onReauthFlow: (flow: FlowEnum) => void;
}) {
  const [error, setError] = useState<string>('');

  const recoveryCodesQuery = useQuery({
    enabled: false,
    queryKey: ['mfa-recovery-codes'],
    queryFn: async () => {
      return api
        .post(apiUrl(ApiEndpoints.auth_recovery), undefined, {
          timeout: 30 * 1000
        })
        .catch((error) => {
          setError(
            extractErrorMessage(error, t`Error fetching recovery codes`)
          );

          // A 401 error indicates that re-authentication is required
          if (error.status === 401) {
            const flow = getReauthFlow(error);
            if (flow !== null) {
              setOpen(false);
              onReauthFlow(flow);
            }
          } else {
            queryClient.cancelQueries({ queryKey: ['mfa-recovery-codes'] });
          }

          throw error;
        });
    }
  });

  const unusedCodes = useMemo(() => {
    return recoveryCodesQuery.data?.data?.data?.unused_codes ?? [];
  }, [recoveryCodesQuery.data]);

  useEffect(() => {
    setError('');

    // Re-fetch codes on opened
    if (opened) {
      recoveryCodesQuery.refetch();
    }
  }, [opened]);

  return (
    <Modal
      opened={opened}
      onClose={() => setOpen(false)}
      title={<StylishText size='lg'>{t`Recovery Codes`}</StylishText>}
    >
      <Stack>
        <Divider />
        {error && (
          <Alert color='red' icon={<IconExclamationCircle />} title={t`Error`}>
            {error}
          </Alert>
        )}
        {recoveryCodesQuery.isFetching || recoveryCodesQuery.isLoading ? (
          <Loader />
        ) : unusedCodes.length > 0 ? (
          <Stack gap='xs'>
            <Alert
              color='blue'
              icon={<IconInfoCircle />}
              title={t`Recovery Codes`}
            >
              <Trans>
                The following one time recovery codes are available for use
              </Trans>
            </Alert>
            <Paper p='sm' withBorder>
              <Stack gap='xs'>
                {unusedCodes.map((code: string) => (
                  <Group
                    p={3}
                    justify='space-between'
                    key={`mfa-recovery-code-${code}`}
                  >
                    <Text>{code}</Text>
                  </Group>
                ))}
                <Divider />
                <Group justify='space-between'>
                  <Trans>Copy recovery codes to clipboard</Trans>
                  <CopyButton value={unusedCodes.join('\n')} />
                </Group>
              </Stack>
            </Paper>
          </Stack>
        ) : (
          <Alert
            color='yellow'
            icon={<IconAlertCircle />}
            title={t`No Unused Codes`}
          >
            <Trans>There are no available recovery codes</Trans>
          </Alert>
        )}
        <Divider />
        <Group justify='right'>
          <Button onClick={() => setOpen(false)}>
            <Trans>Close</Trans>
          </Button>
        </Group>
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
  const navigate = useNavigate();

  // Fetch list of MFA methods currently configured for the user
  const { isLoading, data, refetch } = useQuery({
    queryKey: ['mfa-list'],
    queryFn: () =>
      api
        .get(apiUrl(ApiEndpoints.auth_authenticators))
        .then((res) => res?.data?.data ?? [])
        .catch(() => [])
  });

  const refetchAfterRemoval = () => {
    refetch();
    if (
      data == undefined &&
      useGlobalSettingsState.getState().isSet('LOGIN_ENFORCE_MFA')
    ) {
      console.log('MFA enforced but no MFA methods remain - logging out now');
      doLogout(navigate);
    }
  };

  // Memoize the list of currently used MFA factors
  const usedFactors: string[] = useMemo(() => {
    if (isLoading || !data) return [];
    return data.map((token: any) => token.type);
  }, [isLoading, data]);

  const [webauthnToken, setWebauthnToken] = useState<number | null>(null);

  const [recoveryCodesOpen, setRecoveryCodesOpen] = useState<boolean>(false);
  const [reauthPassOpen, setReauthPassModalOpen] = useState<boolean>(false);
  const [reauthTOTPOpen, setReauthTOTPModalOpen] = useState<boolean>(false);
  const [registerTOTPModalOpen, setRegisterTOTPModalOpen] =
    useState<boolean>(false);
  const [removeTOTPModalOpen, setRemoveTOTPModalOpen] =
    useState<boolean>(false);
  const [removeWebauthnModalOpen, setRemoveWebauthnModalOpen] =
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
    setRecoveryCodesOpen(true);
  }, []);

  // Register a WebAuthn credential with the provided key
  const registerWebauthn = useCallback((key: any) => {
    create({
      publicKey: PublicKeyCredential.parseCreationOptionsFromJSON(key)
    }).then((credential) => {
      const credentialString: string = JSON.stringify(credential);

      api
        .post(
          apiUrl(ApiEndpoints.auth_webauthn),
          {
            name: 'Master Key',
            credential: credentialString
          },
          {
            timeout: 30 * 1000
          }
        )
        .then((response) => {
          showNotification({
            title: t`WebAuthn Registered`,
            message: t`WebAuthn credential registered successfully`,
            color: 'green',
            icon: <IconCircleCheck />
          });
          refetch();
        })
        .catch((error) => {
          const errorMsg = extractErrorMessage(
            error,
            t`Error registering WebAuthn credential`
          );
          showNotification({
            title: t`WebAuthn Registration Failed`,
            message: `${t`Failed to register WebAuthn credential`}: ${errorMsg}`,
            color: 'red',
            icon: <IconExclamationCircle />
          });
        });
    });
  }, []);

  // Request a WebAuthn registration challenge from the server
  const requestWebauthn = useCallback(() => {
    api
      .get(apiUrl(ApiEndpoints.auth_webauthn))
      .then((response) => {
        // Extract credential creation options from the response
        const options = response.data?.data?.creation_options;
        if (options) {
          registerWebauthn(options.publicKey);
        }
        return response.data;
      })
      .catch((error) => {
        const errorMsg: string = extractErrorMessage(
          error,
          t`Error fetching WebAuthn registration`
        );

        // A 401 error indicates that re-authentication is required
        if (error.status === 401) {
          const flow = getReauthFlow(error);
          if (flow !== null) {
            reauthenticate(flow);
          }
        } else {
          showNotification({
            title: t`Error`,
            message: errorMsg,
            color: 'red',
            icon: <IconExclamationCircle />
          });
        }

        throw error;
      });
  }, []);

  const removeTOTP = useCallback(() => {
    setRemoveTOTPModalOpen(true);
  }, []);

  const viewRecoveryCodes = useCallback(() => {
    setRecoveryCodesOpen(true);
  }, []);

  const removeWebauthn = useCallback((id: number) => {
    setWebauthnToken(id);
    setRemoveWebauthnModalOpen(true);
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
        function: requestWebauthn,
        used: usedFactors?.includes('webauthn')
      }
    ].filter((factor) => {
      return auth_config?.mfa?.supported_types.includes(factor.type);
    });
  }, [usedFactors, auth_config]);

  const mfaRows = useMemo(() => {
    return (
      data?.map((token: any) => (
        <Table.Tr key={`${token.created_at}-${token.type}`}>
          <Table.Td>{token.type}</Table.Td>
          <Table.Td>{parseDate(token.last_used_at)}</Table.Td>
          <Table.Td>{parseDate(token.created_at)}</Table.Td>
          <Table.Td>
            <Group grow>
              {token.type == 'totp' && (
                <Button
                  aria-label={'remove-totp'}
                  color='red'
                  onClick={removeTOTP}
                >
                  <Trans>Remove</Trans>
                </Button>
              )}
              {token.type == 'recovery_codes' && (
                <Button
                  aria-label={'view-recovery-codes'}
                  onClick={viewRecoveryCodes}
                >
                  <Trans>View</Trans>
                </Button>
              )}
              {token.type == 'webauthn' && (
                <Button
                  aria-label={'remove-webauthn'}
                  color='red'
                  onClick={() => {
                    removeWebauthn(token.id);
                  }}
                >
                  <Trans>Remove</Trans>
                </Button>
              )}
            </Group>
          </Table.Td>
        </Table.Tr>
      )) ?? []
    );
  }, [data]);

  return (
    <>
      <RecoveryCodesModal
        opened={recoveryCodesOpen}
        setOpen={setRecoveryCodesOpen}
        onReauthFlow={reauthenticate}
      />
      <RemoveTOTPModal
        opened={removeTOTPModalOpen}
        setOpen={setRemoveTOTPModalOpen}
        onReauthFlow={reauthenticate}
        onSuccess={refetchAfterRemoval}
      />
      <RemoveWebauthnModal
        tokenId={webauthnToken}
        opened={removeWebauthnModalOpen}
        setOpen={setRemoveWebauthnModalOpen}
        onReauthFlow={reauthenticate}
        onSuccess={refetchAfterRemoval}
      />
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
                  aria-label={`add-factor-${factor.type}`}
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
