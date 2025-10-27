import {
  type CredentialRequestOptionsJSON,
  get,
  parseRequestOptionsFromJSON
} from '@github/webauthn-json/browser-ponyfill';
import { ApiEndpoints, apiUrl } from '@lib/index';
import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import { Button, Checkbox, TextInput } from '@mantine/core';
import { useForm } from '@mantine/form';
import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useShallow } from 'zustand/react/shallow';
import { api } from '../../App';
import { handleMfaLogin } from '../../functions/auth';
import { useServerApiState } from '../../states/ServerApiState';
import { Wrapper } from './Layout';

export default function Mfa() {
  const simpleForm = useForm({ initialValues: { code: '', remember: false } });
  const navigate = useNavigate();
  const location = useLocation();
  const [loginError, setLoginError] = useState<string | undefined>(undefined);
  const [mfa_context] = useServerApiState(
    useShallow((state) => [state.mfa_context])
  );
  const [webauthn_challenge, setWebauthnChallenge] = useState<string | null>();
  const mfa_types = mfa_context?.types || [];

  useEffect(() => {
    // Extract webauthn challenge if the type is available and not already set
    if (
      (mfa_types.includes('webauthn') || mfa_types.includes('webauthn_2fa')) &&
      !webauthn_challenge
    ) {
      api
        .get(apiUrl(ApiEndpoints.auth_webauthn_login))
        .catch(() => {})
        .then((response) => {
          if (response && response.status === 200) {
            const challenge = response.data.data.request_options;
            setWebauthnChallenge(challenge);
          }
        });
    }
  }, [mfa_types, webauthn_challenge]);

  // try webauthn login automatically if available
  useEffect(() => {
    if (webauthn_challenge) {
      webauthnLoginTry(webauthn_challenge as CredentialRequestOptionsJSON);
    }
  }, [webauthn_challenge]);

  return (
    <Wrapper titleText={t`Multi-Factor Authentication`} logOff>
      {(mfa_types.includes('recovery_codes') || mfa_types.includes('totp')) && (
        <TextInput
          required
          label={t`TOTP Code`}
          name='TOTP'
          description={t`Enter one of your codes: ${mfa_types}`}
          {...simpleForm.getInputProps('code')}
          error={loginError}
        />
      )}

      <Checkbox
        label={t`Remember this device`}
        name='remember'
        description={t`If enabled, you will not be asked for MFA on this device for 30 days.`}
        {...simpleForm.getInputProps('remember', { type: 'checkbox' })}
      />
      <Button
        type='submit'
        onClick={() =>
          handleMfaLogin(navigate, location, simpleForm.values, setLoginError)
        }
      >
        <Trans>Log in</Trans>
      </Button>
    </Wrapper>
  );
}

async function webauthnLoginTry(
  webauthn_challenge: CredentialRequestOptionsJSON
) {
  try {
    const options = parseRequestOptionsFromJSON(webauthn_challenge);
    const credential = await get(options);
    const reauthResp = await api.post(ApiEndpoints.auth_webauthn_login, {
      credential: credential
    });
  } catch (e) {
    console.error(e);
  }
}
