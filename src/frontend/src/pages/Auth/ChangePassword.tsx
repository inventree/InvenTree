import { Trans, t } from '@lingui/macro';
import {
  Button,
  Center,
  Container,
  Divider,
  Group,
  Paper,
  PasswordInput,
  Stack,
  Text
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { useNavigate } from 'react-router-dom';

import { api } from '../../App';
import { StylishText } from '../../components/items/StylishText';
import { ProtectedRoute } from '../../components/nav/Layout';
import { LanguageContext } from '../../contexts/LanguageContext';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { clearCsrfCookie } from '../../functions/auth';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';

export default function Set_Password() {
  const simpleForm = useForm({
    initialValues: {
      current_password: '',
      new_password1: '',
      new_password2: ''
    }
  });

  const user = useUserState();
  const navigate = useNavigate();

  function passwordError(values: any) {
    let message: any =
      values?.new_password2 ||
      values?.new_password1 ||
      values?.current_password ||
      values?.error ||
      t`Password could not be changed`;

    // If message is array
    if (!Array.isArray(message)) {
      message = [message];
    }

    message.forEach((msg: string) => {
      notifications.show({
        title: t`Error`,
        message: msg,
        color: 'red'
      });
    });
  }

  function handleSet() {
    const { clearUserState } = useUserState.getState();

    // check if passwords match
    if (simpleForm.values.new_password1 !== simpleForm.values.new_password2) {
      passwordError({ new_password2: t`Passwords do not match` });
      return;
    }

    // Set password with call to backend
    api
      .post(apiUrl(ApiEndpoints.user_change_password), {
        current_password: simpleForm.values.current_password,
        new_password: simpleForm.values.new_password2
      })
      .then((val) => {
        passwordError(val.data);
      })
      .catch((err) => {
        if (err.status === 401) {
          notifications.show({
            title: t`Password Changed`,
            message: t`The password was set successfully. You can now login with your new password`,
            color: 'green',
            autoClose: false
          });
          clearUserState();
          clearCsrfCookie();
          navigate('/login');
        } else {
          // compile errors
          const errors: { [key: string]: string[] } = {};
          for (const val of err.response.data.errors) {
            if (!errors[val.param]) {
              errors[val.param] = [];
            }
            errors[val.param].push(val.message);
          }
          passwordError(errors);
        }
      });
  }

  return (
    <LanguageContext>
      <ProtectedRoute>
        <Center mih='100vh'>
          <Container w='md' miw={425}>
            <Stack>
              <StylishText size='xl'>{t`Reset Password`}</StylishText>
              <Divider />
              {user.username() && (
                <Paper>
                  <Group>
                    <StylishText size='md'>{t`User`}</StylishText>
                    <Text>{user.username()}</Text>
                  </Group>
                </Paper>
              )}
              <Divider />
              <Stack gap='xs'>
                <PasswordInput
                  required
                  aria-label='password'
                  label={t`Current Password`}
                  description={t`Enter your current password`}
                  {...simpleForm.getInputProps('current_password')}
                />
                <PasswordInput
                  required
                  aria-label='input-password-1'
                  label={t`New Password`}
                  description={t`Enter your new password`}
                  {...simpleForm.getInputProps('new_password1')}
                />
                <PasswordInput
                  required
                  aria-label='input-password-2'
                  label={t`Confirm New Password`}
                  description={t`Confirm your new password`}
                  {...simpleForm.getInputProps('new_password2')}
                />
              </Stack>
              <Button type='submit' onClick={handleSet}>
                <Trans>Confirm</Trans>
              </Button>
            </Stack>
          </Container>
        </Center>
      </ProtectedRoute>
    </LanguageContext>
  );
}
