import { Trans, t } from '@lingui/macro';
import { Center, Container, Group, Select, Stack, Text } from '@mantine/core';
import { useToggle } from '@mantine/hooks';
import { useEffect } from 'react';

import { AuthenticationForm } from '../../components/forms/AuthenticationForm';
import { HostOptionsForm } from '../../components/forms/HostOptionsForm';
import { EditButton } from '../../components/items/EditButton';
import { defaultHostKey } from '../../defaults';
import { useLocalState } from '../../states/LocalState';
import { HostList } from '../../states/states';

export default function Login() {
  const [hostKey, setHost, hostList] = useLocalState((state) => [
    state.hostKey,
    state.setHost,
    state.hostList
  ]);
  const hostname =
    hostList[hostKey] === undefined ? t`No selection` : hostList[hostKey].name;
  const [hostEdit, setHostEdit] = useToggle([false, true] as const);
  const hostListData = Object.keys(hostList).map((key) => ({
    value: key,
    label: hostList[key].name
  }));
  const [HostListEdit, setHostListEdit] = useToggle([false, true] as const);

  // Data manipulation functions
  function ChangeHost(newHost: string) {
    setHost(hostList[newHost].host, newHost);
    setHostEdit(false);
  }
  function SaveOptions(newHostList: HostList) {
    useLocalState.setState({ hostList: newHostList });
    if (newHostList[hostKey] === undefined) {
      setHost('', '');
    }
    setHostListEdit();
  }
  // Set default host to localhost if no host is selected
  useEffect(() => {
    if (hostKey === '') {
      ChangeHost(defaultHostKey);
    }
  }, []);

  // Subcomponents
  function SelectHost() {
    if (!hostEdit) return null;
    return (
      <Group>
        <Select
          value={hostKey}
          onChange={ChangeHost}
          data={hostListData}
          disabled={HostListEdit}
        />
        {EditButton(setHostListEdit, HostListEdit, HostListEdit)}
      </Group>
    );
  }

  function EditHostList() {
    if (!HostListEdit) return null;
    return (
      <>
        <Text>
          <Trans>Edit host options</Trans>
        </Text>
        <HostOptionsForm data={hostList} saveOptions={SaveOptions} />
      </>
    );
  }

  return (
    <Center mih="100vh">
      <Container w="md" miw={400}>
        <Stack>
          <EditHostList />
          {!HostListEdit && (
            <AuthenticationForm
              hostname={hostname}
              editing={hostEdit}
              setEditing={setHostEdit}
              selectElement={<SelectHost />}
            />
          )}
        </Stack>
      </Container>
    </Center>
  );
}
