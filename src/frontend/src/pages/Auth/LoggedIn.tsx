import { Trans } from '@lingui/macro';
import { Group, Loader, Text } from '@mantine/core';
import { useDebouncedCallback } from '@mantine/hooks';
import { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

import { checkLoginState } from '../../functions/auth';
import { Wrapper } from './LoginLayoutComponent';

export default function Logged_In() {
  const navigate = useNavigate();
  const location = useLocation();

  const checkLoginStateDebounced = useDebouncedCallback(checkLoginState, 300);

  useEffect(() => {
    checkLoginStateDebounced(navigate, location?.state);
  }, [navigate]);

  return (
    <Wrapper>
      <Text size='lg'>
        <Trans>Checking if you are already logged in</Trans>
      </Text>
      <Group justify='center'>
        <Loader />
      </Group>
    </Wrapper>
  );
}
