import { Trans, t } from '@lingui/macro';
import {
  Button,
  Divider,
  Group,
  Paper,
  PasswordInput,
  Stack,
  Text
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { useNavigate } from 'react-router-dom';
import { StylishText } from '../../components/items/StylishText';
import { handleChangePassword } from '../../functions/auth';
import { useUserState } from '../../states/UserState';
import { Wrapper } from './Layout';

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

  return (
    <Wrapper titleText={t`Reset Password`}>
      {user.username() && (
        <Paper>
          <Group>
            <StylishText size='md'>{t`User`}</StylishText>
            <Text>{user.username()}</Text>
          </Group>
        </Paper>
      )}
      <Divider p='xs' />
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
      <Button
        type='submit'
        onClick={() =>
          handleChangePassword(
            simpleForm.values.new_password1,
            simpleForm.values.new_password2,
            simpleForm.values.current_password,
            navigate
          )
        }
        disabled={
          simpleForm.values.current_password === '' ||
          simpleForm.values.new_password1 === ''
        }
      >
        <Trans>Confirm</Trans>
      </Button>
    </Wrapper>
  );
}
