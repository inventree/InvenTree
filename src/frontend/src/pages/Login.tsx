import { useNavigate } from 'react-router-dom';
import { Center, Container, Group, Select, Text, Stack } from '@mantine/core';
import { useAuth } from '../context/AuthContext';
import { AuthenticationForm } from '../components/AuthenticationForm';
import { useLocalState } from '../context/LocalState';
import { useToggle } from '@mantine/hooks';
import { EditButton } from '../components/items/EditButton';
import { HostOptionsForm } from '../components/HostOptionsForm';
import { HostList } from '../context/states';
import { Trans, t } from '@lingui/macro';
import { useApiState } from '../context/ApiState';

export function Login() {
  const { handleLogin } = useAuth();
  const navigate = useNavigate();
  const [hostKey, setHost, hostList, lastUsername] = useLocalState((state) => [
    state.hostKey,
    state.setHost,
    state.hostList,
    state.lastUsername
  ]);
  const [fetchApiState] = useApiState((state) => [state.fetchApiState]);
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

  // Main functions
  function Login(username: string, password: string) {
    handleLogin(username, password).then(() => {
      useLocalState.setState({ lastUsername: username });
      navigate('/');
    });
    fetchApiState();
  }
  function Register(name: string, username: string, password: string) {
    // TODO: Register
    console.log('Registering is not implemented yet');
    console.log(name, username, password);
  }

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
              Login={Login}
              Register={Register}
              hostname={hostname}
              lastUsername={lastUsername}
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
