import { Trans } from '@lingui/macro';
import { Text } from '@mantine/core';
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { checkLoginState } from '../../functions/auth';

export default function Logged_In() {
  const navigate = useNavigate();

  useEffect(() => {
    checkLoginState(navigate);
  }, []);

  return (
    <>
      <Text>
        <Trans>Checking if you are already logged in</Trans>
      </Text>
    </>
  );
}
