import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import { Button, Checkbox, Code, TextInput } from '@mantine/core';
import { useForm } from '@mantine/form';
import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useShallow } from 'zustand/react/shallow';
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

  const mfa_types = mfa_context?.types || [];
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
      {(mfa_types.includes('webauthn') ||
        mfa_types.includes('webauthn_2fa')) && (
        <Code>
          {t`Please use your WebAuthn device to authenticate. If you have multiple devices, select the one you want to use.`}
        </Code>
      )}
      {(mfa_types.includes('webauthn') ||
        mfa_types.includes('webauthn_2fa')) && (
        <TextInput
          required
          label={t`WebAuthn Device`}
          name='webauthn'
          description={t`Select your WebAuthn device from the list.`}
          {...simpleForm.getInputProps('webauthn')}
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
