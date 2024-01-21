import { Trans, t } from '@lingui/macro';
import { Center, Container, Paper, Text } from '@mantine/core';
import { useDisclosure, useToggle } from '@mantine/hooks';
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { setApiDefaults } from '../../App';
import { AuthFormOptions } from '../../components/forms/AuthFormOptions';
import {
  AuthenticationForm,
  ModeSelector,
  RegistrationForm
} from '../../components/forms/AuthenticationForm';
import { InstanceOptions } from '../../components/forms/InstanceOptions';
import { defaultHostKey } from '../../defaults/defaultHostList';
import { checkLoginState } from '../../functions/auth';
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

  // Data manipulation functions
  function ChangeHost(newHost: string): void {
    setHost(hostList[newHost]?.host, newHost);
    setApiDefaults();
    fetchServerApiState();
  }

  // Set default host to localhost if no host is selected
  useEffect(() => {
    if (hostKey === '') {
      ChangeHost(defaultHostKey);
    }

    // check if user is logged in in PUI
    checkLoginState(navigate, undefined, true);
  }, []);
  // Fetch server data on mount if no server data is present
  useEffect(() => {
    if (server.server === null) {
      fetchServerApiState();
    }
  }, [server]);

  // Main rendering block
  return (
    <Center mih="100vh">
      <Container w="md" miw={400}>
        {hostEdit ? (
          <InstanceOptions
            hostKey={hostKey}
            ChangeHost={ChangeHost}
            setHostEdit={setHostEdit}
          />
        ) : (
          <>
            <Paper radius="md" p="xl" withBorder>
              <Text size="lg" weight={500}>
                <Trans>Welcome, log in below</Trans>
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
