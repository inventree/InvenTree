import { useNavigate } from 'react-router-dom';
import { Center, Container, Group, Select, Stack } from '@mantine/core';
import { useAuth } from '../contex/AuthContext';
import { AuthenticationForm } from '../components/AuthenticationForm';
import { useLocalState } from '../contex/LocalState';
import { fetchSession } from '../App';
import { useToggle } from '@mantine/hooks';
import { EditButton } from '../components/items/EditButton';

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


  // Subcomponents
  function HostSelect() {
    if (!editing)
      return null;
    return <Group>
      <Select value={hostKey} onChange={changeHost} data={hostOptionsSelect} />
      {EditButton(setOptionEditing, optionEditing)}
    </Group>
  }

  return (
    <Center mih="100vh">
      <Container w="md">
        <Stack>
          <HostSelect />
          <AuthenticationForm
            Login={Login}
            Register={Register}
            hostname={hostname}
            lastUsername={lastUsername}
            editing={editing}
            setEditing={setEditing}
          />
        </Stack>
      </Container>
    </Center>
  );
}
