import { Group, Loader } from '@mantine/core';
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { doLogout } from '../../functions/auth';
import { Wrapper } from './LoginLayoutComponent';

/* Expose a route for explicit logout via URL */
export default function Logout() {
  const navigate = useNavigate();

  useEffect(() => {
    doLogout(navigate);
  }, []);

  return (
    <Wrapper titleText='Logging out'>
      <Group justify='center'>
        <Loader />
      </Group>
    </Wrapper>
  );
}
