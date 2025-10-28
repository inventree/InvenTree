import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import { Button, Checkbox, TextInput } from '@mantine/core';
import { useForm } from '@mantine/form';
import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useShallow } from 'zustand/react/shallow';
import { handleMfaLogin, handleWebauthnLogin } from '../../functions/auth';
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

  useEffect(() => {
    if (mfa_types.includes('webauthn') || mfa_types.includes('webauthn_2fa')) {
      handleWebauthnLogin(navigate, location);
    }
  }, [mfa_types]);

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
