import { Trans, t } from '@lingui/macro';
import { Button, PasswordInput } from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { handlePasswordReset } from '../../functions/auth';
import { Wrapper } from './Layout';

export default function ResetPassword() {
  const simpleForm = useForm({ initialValues: { password: '' } });
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const key = searchParams.get('key');

  // make sure we have a key
  useEffect(() => {
    if (!key) {
      notifications.show({
        title: t`Key invalid`,
        message: t`You need to provide a valid key to set a new password. Check your inbox for a reset link.`,
        color: 'red',
        autoClose: false
      });
    }
  }, [key]);

  return (
    <Wrapper titleText={t`Set new password`}>
      <PasswordInput
        required
        label={t`Password`}
        description={t`The desired new password`}
        {...simpleForm.getInputProps('password')}
      />
      <Button
        type='submit'
        onClick={() =>
          handlePasswordReset(key, simpleForm.values.password, navigate)
        }
      >
        <Trans>Send Password</Trans>
      </Button>
    </Wrapper>
  );
}
