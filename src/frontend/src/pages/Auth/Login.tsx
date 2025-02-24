import { Trans, t } from '@lingui/macro';
import { Anchor, Divider, Text } from '@mantine/core';
import { useToggle } from '@mantine/hooks';
import { useEffect, useMemo } from 'react';
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import { setApiDefaults } from '../../App';
import { AuthFormOptions } from '../../components/forms/AuthFormOptions';
import { AuthenticationForm } from '../../components/forms/AuthenticationForm';
import { InstanceOptions } from '../../components/forms/InstanceOptions';
import { defaultHostKey } from '../../defaults/defaultHostList';
import {
  checkLoginState,
  doBasicLogin,
  followRedirect
} from '../../functions/auth';
import { useServerApiState } from '../../states/ApiState';
import { useLocalState } from '../../states/LocalState';
import { Wrapper } from './Layout';

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
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const [sso_registration, registration_enabled] = useServerApiState(
    (state) => [state.sso_registration_enabled, state.registration_enabled]
  );
  const both_reg_enabled =
    registration_enabled() || sso_registration() || false;

  const LoginMessage = useMemo(() => {
    const val = server.customize?.login_message;
    if (val == undefined) return null;
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

  return (
    <>
      {hostEdit ? (
        <InstanceOptions
          hostKey={hostKey}
          ChangeHost={ChangeHost}
          setHostEdit={setHostEdit}
        />
      ) : (
        <>
          <Wrapper titleText={t`Login`} smallPadding>
            <AuthenticationForm />
            {both_reg_enabled === false && (
              <Text ta='center' size={'xs'} mt={'md'}>
                <Trans>Don&apos;t have an account?</Trans>{' '}
                <Anchor
                  component='button'
                  type='button'
                  c='dimmed'
                  size='xs'
                  onClick={() => navigate('/register')}
                >
                  <Trans>Register</Trans>
                </Anchor>
              </Text>
            )}
            {LoginMessage}
          </Wrapper>
          <AuthFormOptions hostname={hostname} toggleHostEdit={setHostEdit} />
        </>
      )}
    </>
  );
}
