import { Trans } from '@lingui/react/macro';
import {
  Button,
  Divider,
  Group,
  Loader,
  Paper,
  Stack
} from '@mantine/core';
import { Outlet, useNavigate } from 'react-router-dom';
import SplashScreen from '../../components/SplashScreen';
import { doLogout } from '../../functions/auth';
import './Auth.css';

export default function LoginLayoutComponent() {
  return (
    <SplashScreen>
      <div className='auth-layout-root'>
        <div className='auth-layout-container'>
          <Outlet />
        </div>
      </div>
    </SplashScreen>
  );
}

export function Wrapper({
  children,
  titleText,
  logOff = false,
  loader = false,
  smallPadding = false,
  imageOverlay
}: Readonly<{
  children?: React.ReactNode;
  titleText: string;
  logOff?: boolean;
  loader?: boolean;
  smallPadding?: boolean;
  imageOverlay?: React.ReactNode;
}>) {
  const navigate = useNavigate();
  const isLoginPage =
    typeof titleText === 'string' && titleText.toLowerCase().includes('login');

  return (
    <div className='auth-card-container'>
      <div className='auth-form-column'>
        <Stack gap={smallPadding ? 0 : 'md'}>
          <h1 className='auth-welcome-title'>
            {isLoginPage ? 'Login' : titleText}
          </h1>
          {isLoginPage && (
            <p className='auth-welcome-subtitle'>
              Welcome back please login to your account
            </p>
          )}

          {loader && (
            <Group justify='center' my='md'>
              <Loader color='#0284c7' />
            </Group>
          )}
          {children}
          {logOff && (
            <>
              <Divider my='md' />
              <Button
                onClick={() => doLogout(navigate)}
                color='red'
                className='auth-submit-btn'
                style={{ background: '#e03131' }}
              >
                <Trans>Log off</Trans>
              </Button>
            </>
          )}
          {imageOverlay && (
            <div className='auth-mobile-options-container'>
              {imageOverlay}
            </div>
          )}
        </Stack>
      </div>

      <div className='auth-image-column'>
        <div className='auth-image-frame'>
          <img
            src='/login_bgimg.jpeg'
            alt='Warehouse & Workshop Management'
            className='auth-banner-image'
          />
          {imageOverlay && (
            <div className='auth-image-controls-overlay'>
              {imageOverlay}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
