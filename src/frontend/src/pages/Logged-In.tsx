import { Trans } from '@lingui/macro';
import { Text } from '@mantine/core';
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../App';
import { ApiPaths, url } from '../context/ApiState';
import { doTokenLogin } from '../functions/auth';

export default function Logged_In() {
  const navigate = useNavigate();

  useEffect(() => {
    api
      .get(url(ApiPaths.user_check))
      .then((val) => {
        if (val.status === 200 && val.data.token) {
          doTokenLogin(val.data.token);
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
