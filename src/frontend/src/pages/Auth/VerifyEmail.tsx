import { Trans, t } from '@lingui/macro';
import { Button, Title } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { apiUrl } from '../../states/ApiState';
import { Wrapper } from './LoginLayoutComponent';

export default function VerifyEmail() {
  const { key } = useParams();
  const navigate = useNavigate();

  function invalidKey() {
    notifications.show({
      title: t`Key invalid`,
      message: t`You need to provide a valid key.`,
      color: 'red'
    });
    navigate('/login');
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
      .post(apiUrl(ApiEndpoints.auth_email_verify), {
        key: key
      })
      .then((val) => {
        if (val.status === 200) {
          navigate('/login');
        }
      });
  }

  return (
    <Wrapper>
      <Title>
        <Trans>Verify Email</Trans>
      </Title>
      <Button type='submit' onClick={handleSet}>
        <Trans>Verify</Trans>
      </Button>
    </Wrapper>
  );
}
