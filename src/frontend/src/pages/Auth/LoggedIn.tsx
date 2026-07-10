import { t } from '@lingui/core/macro';
import { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

import { checkLoginState } from '../../functions/auth';
import { Wrapper } from './Layout';

export default function Logged_In() {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    checkLoginState(navigate, location?.state);
  }, [navigate]);

  return (
    <Wrapper titleText={t`Checking if you are already logged in`} loader />
  );
}
