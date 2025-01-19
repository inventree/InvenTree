import { Trans, t } from '@lingui/macro';
import {
  Button,
  Center,
  Container,
  PasswordInput,
  Stack,
  Title
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { api } from '../../App';
import { LanguageContext } from '../../contexts/LanguageContext';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { apiUrl } from '../../states/ApiState';

export default function ResetPassword() {
  const simpleForm = useForm({ initialValues: { password: '' } });
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const key = searchParams.get('key');

  function invalidKey() {
    notifications.show({
      title: t`Key invalid`,
      message: t`You need to provide a valid key to set a new password. Check your inbox for a reset link.`,
      color: 'red'
    });
    navigate('/login');
  }

  function success() {
    notifications.show({
      title: t`Password set`,
      message: t`The password was set successfully. You can now login with your new password`,
      color: 'green',
      autoClose: false
    });
    navigate('/login');
  }

  function passwordError(values: any) {
    notifications.show({
      title: t`Reset failed`,
      message: values?.errors.map((e: any) => e.message).join('\n'),
      color: 'red'
    });
  }

  useEffect(() => {
    // make sure we have a key
    if (!key) {
      invalidKey();
    }
  }, [key]);

  function handleSet() {
    // Set password with call to backend
    api
      .post(
        apiUrl(ApiEndpoints.user_reset_set),
        {
          key: key,
          password: simpleForm.values.password
        },
        { headers: { Authorization: '' } }
      )
      .then((val) => {
        if (val.status === 200) {
          success();
        } else {
          passwordError(val.data);
        }
      })
      .catch((err) => {
        if (err.response?.status === 400) {
          passwordError(err.response.data);
        } else if (err.response?.status === 401) {
          success();
        } else {
          passwordError(err.response.data);
        }
      });
  }

  return (
    <LanguageContext>
      <Center mih='100vh'>
        <Container w='md' miw={425}>
          <Stack>
            <Title>
              <Trans>Set new password</Trans>
            </Title>
            <Stack>
              <PasswordInput
                required
                label={t`Password`}
                description={t`We will send you a link to login - if you are registered`}
                {...simpleForm.getInputProps('password')}
              />
            </Stack>
            <Button type='submit' onClick={handleSet}>
              <Trans>Send Email</Trans>
            </Button>
          </Stack>
        </Container>
      </Center>
    </LanguageContext>
  );
}
