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
import { ApiPaths } from '../../enums/ApiEndpoints';
import { apiUrl } from '../../states/ApiState';

export default function Set_Password() {
  const simpleForm = useForm({ initialValues: { password: '' } });
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const token = searchParams.get('token');
  const uid = searchParams.get('uid');

  function invalidToken() {
    notifications.show({
      title: t`Token invalid`,
      message: t`You need to provide a valid token to set a new password. Check your inbox for a reset link.`,
      color: 'red'
    });
    navigate('/login');
  }

  function passwordError(values: any) {
    notifications.show({
      title: t`Reset failed`,
      message: values?.new_password2 || values?.new_password1 || values?.token,
      color: 'red'
    });
  }

  useEffect(() => {
    // make sure we have a token
    if (!token || !uid) {
      notifications.show({
        title: t`No token provided`,
        message: t`You need to provide a token to set a new password. Check your inbox for a reset link.`,
        color: 'red'
      });
      navigate('/login');
    }
  }, [token]);

  function handleSet() {
    // Set password with call to backend
    api
      .post(
        apiUrl(ApiPaths.user_reset_set),
        {
          uid: uid,
          token: token,
          new_password1: simpleForm.values.password,
          new_password2: simpleForm.values.password
        },
        { headers: { Authorization: '' } }
      )
      .then((val) => {
        if (val.status === 200) {
          notifications.show({
            title: t`Password set`,
            message: t`The password was set successfully. You can now login with your new password`,
            color: 'green',
            autoClose: false
          });
          navigate('/login');
        } else {
          passwordError(val.data);
        }
      })
      .catch((err) => {
        if (
          err.response.status === 400 &&
          err.response.data?.token == 'Invalid value'
        ) {
          invalidToken();
        } else {
          passwordError(err.response.data);
        }
      });
  }

  return (
    <LanguageContext>
      <Center mih="100vh">
        <Container w="md" miw={425}>
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
            <Button type="submit" onClick={handleSet}>
              <Trans>Send mail</Trans>
            </Button>
          </Stack>
        </Container>
      </Center>
    </LanguageContext>
  );
}
