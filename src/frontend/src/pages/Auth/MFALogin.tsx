import { Trans, t } from '@lingui/macro';
import {
  Button,
  Center,
  Container,
  Stack,
  TextInput,
  Title
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { useLocation, useNavigate } from 'react-router-dom';

import { LanguageContext } from '../../contexts/LanguageContext';
import { handleMfaLogin } from '../../functions/auth';

export default function MFALogin() {
  const simpleForm = useForm({ initialValues: { code: '' } });
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <LanguageContext>
      <Center mih='100vh'>
        <Container w='md' miw={425}>
          <Stack>
            <Title>
              <Trans>MFA Login</Trans>
            </Title>
            <Stack>
              <TextInput
                required
                label={t`TOTP Code`}
                name='TOTP'
                description={t`Enter your TOTP or recovery code`}
                {...simpleForm.getInputProps('code')}
              />
            </Stack>
            <Button
              type='submit'
              onClick={() =>
                handleMfaLogin(navigate, location, simpleForm.values)
              }
            >
              <Trans>Log in</Trans>
            </Button>
          </Stack>
        </Container>
      </Center>
    </LanguageContext>
  );
}
