import { t } from '@lingui/macro';
import {
  BackgroundImage,
  Center,
  Container,
  Divider,
  Paper,
  Text
} from '@mantine/core';
import { useDisclosure, useToggle } from '@mantine/hooks';
import { useEffect, useMemo } from 'react';
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import { setApiDefaults } from '../../App';
import { AuthFormOptions } from '../../components/forms/AuthFormOptions';
import {
  AuthenticationForm,
  ModeSelector,
  RegistrationForm
} from '../../components/forms/AuthenticationForm';
import { InstanceOptions } from '../../components/forms/InstanceOptions';
import { StylishText } from '../../components/items/StylishText';
import { defaultHostKey } from '../../defaults/defaultHostList';
import {
  checkLoginState,
  doBasicLogin,
  followRedirect
} from '../../functions/auth';
import { generateUrl } from '../../functions/urls';
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

  useEffect(() => {
    if (location.pathname === '/register') {
      setMode.close();
    } else {
      setMode.open();
    }
  }, [location]);

  const LoginMessage = useMemo(() => {
    const val = server.customize?.login_message;
    if (val) {
      return (
        <>
          <Divider my='md' />
          <Text>
            <span
              // biome-ignore lint/security/noDangerouslySetInnerHtml: <explanation>
              dangerouslySetInnerHTML={{ __html: val }}
            />
          </Text>
        </>
      );
    }
    return null;
  }, [server.customize]);

  const SplashComponent = useMemo(() => {
    const temp = server.customize?.splash;
    if (temp) {
      return ({ children }: { children: React.ReactNode }) => (
        <BackgroundImage src={generateUrl(temp)}>{children}</BackgroundImage>
      );
    }
    return ({ children }: { children: React.ReactNode }) => <>{children}</>;
  }, [server.customize]);

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
        searchParams.get('password') ?? '',
        navigate
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
    <SplashComponent>
      <Center mih='100vh'>
        <div
          style={{
            padding: '10px',
            backgroundColor: 'rgba(0,0,0,0.5)',
            boxShadow: '0 0 15px 10px rgba(0,0,0,0.5)'
          }}
        >
          <Container w='md' miw={400}>
            {hostEdit ? (
              <InstanceOptions
                hostKey={hostKey}
                ChangeHost={ChangeHost}
                setHostEdit={setHostEdit}
              />
            ) : (
              <>
                <Paper p='xl' withBorder>
                  <StylishText size='xl'>
                    {loginMode ? t`Login` : t`Register`}
                  </StylishText>
                  <Divider p='xs' />
                  {loginMode ? <AuthenticationForm /> : <RegistrationForm />}
                  <ModeSelector
                    loginMode={loginMode}
                    changePage={(newPage) => navigate(`/${newPage}`)}
                  />
                  {LoginMessage}
                </Paper>
                <AuthFormOptions
                  hostname={hostname}
                  toggleHostEdit={setHostEdit}
                />
              </>
            )}
          </Container>
        </div>
      </Center>
    </SplashComponent>
  );
}
