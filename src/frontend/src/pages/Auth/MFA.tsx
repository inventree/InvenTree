import { Trans, t } from '@lingui/macro';
import { Button, TextInput, Title } from '@mantine/core';
import { useForm } from '@mantine/form';
import { useLocation, useNavigate } from 'react-router-dom';
import { handleMfaLogin } from '../../functions/auth';
import { Wrapper } from './LoginLayoutComponent';

export default function Mfa() {
  const simpleForm = useForm({ initialValues: { code: '' } });
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Wrapper>
      <Title>
        <Trans>MFA Login</Trans>
      </Title>
      <TextInput
        required
        label={t`TOTP Code`}
        name='TOTP'
        description={t`Enter your TOTP or recovery code`}
        {...simpleForm.getInputProps('code')}
      />
      <Button
        type='submit'
        onClick={() => handleMfaLogin(navigate, location, simpleForm.values)}
      >
        <Trans>Log in</Trans>
      </Button>
    </Wrapper>
  );
}
