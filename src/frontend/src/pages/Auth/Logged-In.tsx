import { Trans, t } from '@lingui/macro';
import { Text } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconCheck } from '@tabler/icons-react';
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { api } from '../../App';
import { doTokenLogin } from '../../functions/auth';
import { ApiPaths, url } from '../../states/ApiState';

export default function Logged_In() {
  const navigate = useNavigate();

  useEffect(() => {
    api
      .get(url(ApiPaths.user_token))
      .then((val) => {
        if (val.status === 200 && val.data.token) {
          doTokenLogin(val.data.token);

          notifications.show({
            title: t`Already logged in`,
            message: t`Found an existing login - using it to log you in.`,
            color: 'green',
            icon: <IconCheck size="1rem" />
          });

          navigate('/home');
        } else {
          navigate('/login');
        }
      })
      .catch(() => {
        navigate('/login');
      });
  }, []);

  return (
    <>
      <Text>
        <Trans>Checking if you are already logged in</Trans>
      </Text>
    </>
  );
}
