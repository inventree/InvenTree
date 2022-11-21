import { useNavigate } from 'react-router-dom';
import { Center, Chip, Container, Stack } from '@mantine/core';
import { useAuth } from '../contex/AuthContext';
import { AuthenticationForm } from '../components/AuthenticationForm';
import { useLocalState } from '../contex/LocalState';
import { fetchSession } from '../App';

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
  }
  const hostname =
    hostOptions[hostKey] === undefined
      ? 'No selection'
      : hostOptions[hostKey].name;

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
      <Stack>
        <Center>
          <Chip.Group
            position="center"
            m="md"
            multiple={false}
            value={hostKey}
            onChange={changeHost}
          >
            {Object.keys(hostOptions).map((key) => (
              <Chip key={key} value={key}>
                {hostOptions[key].name}
              </Chip>
            ))}
          </Chip.Group>
        </Center>
        <Container w="md">
          <AuthenticationForm
            Login={Login}
            Register={Register}
            hostname={hostname}
            lastUsername={lastUsername}
          />
        </Container>
      </Stack>
    </Center>
  );
}
