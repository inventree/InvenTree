import { t } from '@lingui/core/macro';
import { useEffect } from 'react';
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom';

import { checkLoginState } from '../../functions/auth';
import { showLoginNotification } from '../../functions/notifications';
import { Wrapper } from './Layout';

// Maps the 'error' query param allauth appends to this callback URL when an
// SSO login attempt fails server-side (e.g. registration is closed, or the
// user cancelled at the provider) - see on_authentication_error() in
// allauth/headless/socialaccount/internal.py.
function ssoErrorMessage(error: string): string {
  switch (error) {
    case 'signup_closed':
      return t`Registration via SSO is currently disabled.`;
    case 'cancelled':
      return t`Login was cancelled.`;
    case 'denied':
      return t`Access was denied by the identity provider.`;
    case 'permission_denied':
      return t`You do not have permission to log in this way.`;
    case 'reauthentication_required':
      return t`You need to reauthenticate to continue.`;
    default:
      return t`An error occurred during SSO login (${error}).`;
  }
}

export default function Logged_In() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const error = searchParams.get('error');

    if (error) {
      showLoginNotification({
        title: t`SSO Login Failed`,
        message: ssoErrorMessage(error),
        success: false
      });
      navigate('/login');
      return;
    }

    checkLoginState(navigate, location?.state);
  }, [navigate]);

  return (
    <Wrapper titleText={t`Checking if you are already logged in`} loader />
  );
}
