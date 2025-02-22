import { Trans, t } from '@lingui/macro';
import { Button, Center, Container, Stack, Title } from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { LanguageContext } from '../../contexts/LanguageContext';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { authApi, doLogout, followRedirect } from '../../functions/auth';
import { apiUrl } from '../../states/ApiState';
import { QrRegistrationForm } from '../Index/Settings/AccountSettings/QrRegistrationForm';

export default function MFASetup() {
  const navigate = useNavigate();
  const location = useLocation();

  const [totpQr, setTotpQr] = useState<{ totp_url: string; secret: string }>();
  const [value, setValue] = useState('');

  const registerTotp = async () => {
    await authApi(apiUrl(ApiEndpoints.auth_totp), undefined, 'get').catch(
      (err) => {
        if (err.status == 404 && err.response.data.meta.secret) {
          setTotpQr(err.response.data.meta);
        } else {
          const msg = err.response.data.errors[0].message;
          showNotification({
            title: t`Failed to set up MFA`,
            message: msg,
            color: 'red'
          });
        }
      }
    );
  };

  useEffect(() => {
    if (!totpQr) {
      registerTotp();
    }
  }, [totpQr]);

  return (
    <LanguageContext>
      <Center mih='100vh'>
        <Container w='md' miw={425}>
          <Stack>
            <Title>
              <Trans>MFA Setup Required</Trans>
            </Title>
            <QrRegistrationForm
              url={totpQr?.totp_url ?? ''}
              secret={totpQr?.secret ?? ''}
              value={value}
              setValue={setValue}
            />
            <Button
              disabled={!value}
              onClick={() => {
                authApi(apiUrl(ApiEndpoints.auth_totp), undefined, 'post', {
                  code: value
                }).then(() => {
                  followRedirect(navigate, location?.state);
                });
              }}
            >
              <Trans>Add TOTP</Trans>
            </Button>
            <Button onClick={() => doLogout(navigate)} color='red'>
              <Trans>Log off</Trans>
            </Button>
          </Stack>
        </Container>
      </Center>
    </LanguageContext>
  );
}
