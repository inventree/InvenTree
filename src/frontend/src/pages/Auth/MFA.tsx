import { Trans, t } from '@lingui/macro';
import { Button, TextInput } from '@mantine/core';
import { useForm } from '@mantine/form';
import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { handleMfaLogin } from '../../functions/auth';
import { Wrapper } from './Layout';

export default function Mfa() {
  const simpleForm = useForm({ initialValues: { code: '' } });
  const navigate = useNavigate();
  const location = useLocation();
  const [loginError, setLoginError] = useState<string | undefined>(undefined);

  return (
    <Wrapper titleText={t`Multi-Factor Login`} logOff>
      <TextInput
        required
        label={t`TOTP Code`}
        name='TOTP'
        description={t`Enter your TOTP or recovery code`}
        {...simpleForm.getInputProps('code')}
        error={loginError}
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
