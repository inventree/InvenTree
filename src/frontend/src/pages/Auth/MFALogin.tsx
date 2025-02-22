import { Trans, t } from '@lingui/macro';
import {
  Button,
  Center,
  Container,
  Paper,
  Stack,
  TextInput
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { useLocation, useNavigate } from 'react-router-dom';

import { useState } from 'react';
import SplashScreen from '../../components/SplashScreen';
import { StylishText } from '../../components/items/StylishText';
import { LanguageContext } from '../../contexts/LanguageContext';
import { handleMfaLogin } from '../../functions/auth';

export default function MFALogin() {
  const simpleForm = useForm({ initialValues: { code: '' } });
  const navigate = useNavigate();
  const location = useLocation();
  const [loginError, setLoginError] = useState<string | undefined>(undefined);

  return (
    <LanguageContext>
      <SplashScreen>
        <Center mih='100vh'>
          <Container w='md' miw={425}>
            <Paper p='xl' withBorder>
              <Stack>
                <StylishText size='xl'>{t`Multi-Factor Login`}</StylishText>
                <Stack>
                  <TextInput
                    required
                    label={t`TOTP Code`}
                    name='TOTP'
                    description={t`Enter your TOTP or recovery code`}
                    {...simpleForm.getInputProps('code')}
                    error={loginError}
                  />
                </Stack>
                <Button
                  type='submit'
                  onClick={() =>
                    handleMfaLogin(
                      navigate,
                      location,
                      simpleForm.values,
                      setLoginError
                    )
                  }
                >
                  <Trans>Log In</Trans>
                </Button>
              </Stack>
            </Paper>
          </Container>
        </Center>
      </SplashScreen>
    </LanguageContext>
  );
}
