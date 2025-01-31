import { Trans, t } from '@lingui/macro';
import { Center, Container, Paper, Text } from '@mantine/core';
import { useDisclosure, useToggle } from '@mantine/hooks';
import { useEffect } from 'react';
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom';

import { setApiDefaults } from '../../App';
import { AuthFormOptions } from '../../components/forms/AuthFormOptions';
import {
  AuthenticationForm,
  ModeSelector,
  RegistrationForm
} from '../../components/forms/AuthenticationForm';
import { InstanceOptions } from '../../components/forms/InstanceOptions';
import { defaultHostKey } from '../../defaults/defaultHostList';
import {
  checkLoginState,
  doBasicLogin,
  followRedirect
} from '../../functions/auth';
import { useServerApiState } from '../../states/ApiState';
import { useLocalState } from '../../states/LocalState';

export default function Login() {
  const [hostKey, setHost, hostList] = useLocalState((state) => [
    state.hostKey,
    state.setHost,
    state.hostList
  ]);
  const [server, fetchServerApiState] = useServerApiState((state) => [
    state.server,
    state.fetchServerApiState
  ]);
  const hostname =
    hostList[hostKey] === undefined ? t`No selection` : hostList[hostKey]?.name;
  const [hostEdit, setHostEdit] = useToggle([false, true] as const);
  const [loginMode, setMode] = useDisclosure(true);
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();

  // Data manipulation functions
  function ChangeHost(newHost: string | null): void {
    if (newHost === null) return;
    setHost(hostList[newHost]?.host, newHost);
    setApiDefaults();
    fetchServerApiState();
  }

  // Set default host to localhost if no host is selected
  useEffect(() => {
    if (hostKey === '') {
      ChangeHost(defaultHostKey);
    }

    checkLoginState(navigate, location?.state, true);

    // check if we got login params (login and password)
    if (searchParams.has('login') && searchParams.has('password')) {
      doBasicLogin(
        searchParams.get('login') ?? '',
        searchParams.get('password') ?? ''
      ).then(() => {
        followRedirect(navigate, location?.state);
      });
    }
  }, []);

  // Fetch server data on mount if no server data is present
  useEffect(() => {
    if (server.server === null) {
      fetchServerApiState();
    }
  }, [server]);

  // Main rendering block
  return (
    <Center mih='100vh'>
      <Container w='md' miw={400}>
        {hostEdit ? (
          <InstanceOptions
            hostKey={hostKey}
            ChangeHost={ChangeHost}
            setHostEdit={setHostEdit}
          />
        ) : (
          <>
            <Paper radius='md' p='xl' withBorder>
              <Text size='lg' fw={500}>
                {loginMode ? (
                  <Trans>Welcome, log in below</Trans>
                ) : (
                  <Trans>Register below</Trans>
                )}
              </Text>
              {loginMode ? <AuthenticationForm /> : <RegistrationForm />}
              <ModeSelector loginMode={loginMode} setMode={setMode} />
            </Paper>
            <AuthFormOptions hostname={hostname} toggleHostEdit={setHostEdit} />
          </>
        )}
      </Container>
    </Center>
  );
}
