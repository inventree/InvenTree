import { Trans, t } from '@lingui/macro';
import { Button } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { handleVerifyEmail } from '../../functions/auth';
import { Wrapper } from './Layout';

export default function VerifyEmail() {
  const { key } = useParams();
  const navigate = useNavigate();

  // make sure we have a key
  useEffect(() => {
    if (!key) {
      notifications.show({
        title: t`Key invalid`,
        message: t`You need to provide a valid key.`,
        color: 'red'
      });
      navigate('/login');
    }
  }, [key]);

  return (
    <Wrapper titleText={t`Verify Email`}>
      <Button type='submit' onClick={() => handleVerifyEmail(key, navigate)}>
        <Trans>Verify</Trans>
      </Button>
    </Wrapper>
  );
}
