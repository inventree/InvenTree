import { useNavigate } from 'react-router-dom';
import { Center, Container, Select, Stack } from '@mantine/core';
import { useAuth } from '../contex/AuthContext';
import { AuthenticationForm } from '../components/AuthenticationForm';
import { useLocalState } from '../contex/LocalState';
import { fetchSession } from '../App';
import { useToggle } from '@mantine/hooks';

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

  return (
    <Center mih="100vh">
      <Container w="md">
        <Stack>
          {editing ? (<Select value={hostKey} onChange={changeHost} data={hostOptionsSelect} />) : null}
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
