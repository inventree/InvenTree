import { t } from '@lingui/macro';
import { Center, Container } from '@mantine/core';
import { useToggle } from '@mantine/hooks';
import { useEffect } from 'react';

import { setApiDefaults } from '../../App';
import { AuthFormOptions } from '../../components/forms/AuthFormOptions';
import { AuthenticationForm } from '../../components/forms/AuthenticationForm';
import { InstanceOptions } from '../../components/forms/InstanceOptions';
import { defaultHostKey } from '../../defaults/defaultHostList';
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
            <AuthenticationForm />
            <AuthFormOptions hostname={hostname} toggleHostEdit={setHostEdit} />
          </>
        )}
      </Container>
    </Center>
  );
}
