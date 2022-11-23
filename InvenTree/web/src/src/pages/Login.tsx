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
  const [hostKey, setHostValue, hostOptions, lastUsername] = useLocalState(
    (state) => [
      state.hostKey,
      state.setHost,
      state.hostList,
      state.lastUsername
    ]
  );
  function changeHost(newVal: string) {
    setHostValue(hostOptions[newVal].host, newVal);
    setEditing(false);
  }
  const hostname =
    hostOptions[hostKey] === undefined
      ? 'No selection'
      : hostOptions[hostKey].name;

  const [editing, setEditing] = useToggle([false, true] as const);
  const hostOptionsSelect = Object.keys(hostOptions).map((key) => ({ value: key, label: hostOptions[key].name }));
  const [optionEditing, setOptionEditing] = useToggle([false, true] as const);

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

  function SaveOptions(newData: HostList) {
    useLocalState.setState({ hostList: newData });
    if (newData[hostKey] === undefined) { setHostValue('', ''); }
    setOptionEditing();
  }


  // Subcomponents
  function HostSelect() {
    if (!editing)
      return null;
    return <Group>
      <Select value={hostKey} onChange={changeHost} data={hostOptionsSelect} disabled={optionEditing} />
      {EditButton(setOptionEditing, optionEditing, optionEditing)}
    </Group>
  }

  function HostOptionEdit() {
    if (!optionEditing)
      return null;
    return <>
      <Text>Edit host options</Text>
      <HostOptionsForm data={hostOptions} saveOptions={SaveOptions} />
    </>
  }

  return (
    <Center mih="100vh">
      <Container w="md">
        <Stack>
          <HostOptionEdit />
          <HostSelect />
          {!optionEditing &&
            <AuthenticationForm
              Login={Login}
              Register={Register}
              hostname={hostname}
              lastUsername={lastUsername}
              editing={editing}
              setEditing={setEditing}
            />
          }
        </Stack>
      </Container>
    </Center>
  );
}
