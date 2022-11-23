import { useNavigate } from 'react-router-dom';
import { Center, Container, Group, Select, Text, Stack } from '@mantine/core';
import { useAuth } from '../contex/AuthContext';
import { AuthenticationForm } from '../components/AuthenticationForm';
import { useLocalState } from '../contex/LocalState';
import { fetchSession } from '../App';
import { useToggle } from '@mantine/hooks';
import { EditButton } from '../components/items/EditButton';
import { HostOptionsForm } from '../components/HostOptionsForm';
import { HostList } from '../contex/states';

export function Login() {
  const { handleLogin } = useAuth();
  const navigate = useNavigate();
  const [hostKey, setHost, hostList, lastUsername] = useLocalState(
    (state) => [
      state.hostKey,
      state.setHost,
      state.hostList,
      state.lastUsername
    ]
  );
  function changeHost(newHost: string) {
    setHost(hostList[newHost].host, newHost);
    setHostEditing(false);
  }
  const hostname =
    hostList[hostKey] === undefined
      ? 'No selection'
      : hostList[hostKey].name;

  const [hostEditing, setHostEditing] = useToggle([false, true] as const);
  const hostListData = Object.keys(hostList).map((key) => ({ value: key, label: hostList[key].name }));
  const [HostListEditing, setHostListEditing] = useToggle([false, true] as const);

  function Login(username: string, password: string) {
    handleLogin(username, password).then(() => {
      useLocalState.setState({ lastUsername: username });
      navigate('/');
    });
    fetchSession();
  }
  function Register(name: string, username: string, password: string) {
    // TODO: Register
    console.log('Registering is not implemented yet');
    console.log(name, username, password);
  }

  function SaveOptions(newHostList: HostList) {
    useLocalState.setState({ hostList: newHostList });
    if (newHostList[hostKey] === undefined) { setHost('', ''); }
    setHostListEditing();
  }


  // Subcomponents
  function SelectHost() {
    if (!hostEditing)
      return null;
    return <Group>
      <Select value={hostKey} onChange={changeHost} data={hostListData} disabled={HostListEditing} />
      {EditButton(setHostListEditing, HostListEditing, HostListEditing)}
    </Group>
  }

  function EditHostList() {
    if (!HostListEditing)
      return null;
    return <>
      <Text>Edit host options</Text>
      <HostOptionsForm data={hostList} saveOptions={SaveOptions} />
    </>
  }

  return (
    <Center mih="100vh">
      <Container w="md">
        <Stack>
          <EditHostList />
          <SelectHost />
          {!HostListEditing &&
            <AuthenticationForm
              Login={Login}
              Register={Register}
              hostname={hostname}
              lastUsername={lastUsername}
              editing={hostEditing}
              setEditing={setHostEditing}
            />
          }
        </Stack>
      </Container>
    </Center>
  );
}
