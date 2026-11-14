import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import {
  getTotpSecret,
  handleVerifyTotp,
  resendEmailVerification
} from '../../functions/auth';
import { Wrapper } from './Layout';

import { Alert, Button, Group, Stack, Text } from '@mantine/core';
import { useCallback, useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { QrRegistrationForm } from '../Index/Settings/AccountSettings/QrRegistrationForm';

export default function MFASetup() {
  const navigate = useNavigate();
  const location = useLocation();

  const [totpQr, setTotpQr] = useState<{ totp_url: string; secret: string }>();
  const [value, setValue] = useState('');
  const [unverifiedEmail, setUnverifiedEmail] = useState<boolean>(false);
  const [sending, setSending] = useState<boolean>(false);

  const fetchSecret = useCallback(() => {
    setUnverifiedEmail(false);
    getTotpSecret(setTotpQr, () => setUnverifiedEmail(true));
  }, []);

  useEffect(() => {
    fetchSecret();
  }, [fetchSecret]);

  const sendVerification = useCallback(() => {
    setSending(true);
    resendEmailVerification().finally(() => setSending(false));
  }, []);

  if (unverifiedEmail) {
    return (
      <Wrapper titleText={t`MFA Setup Required`} logOff>
        <Stack aria-label='mfa-unverified-email'>
          <Alert color='orange' title={t`Email verification required`}>
            <Text>
              <Trans>
                Your email address must be verified before multi-factor
                authentication can be set up.
              </Trans>
            </Text>
            <Text>
              <Trans>
                Send a verification email, follow the link it contains, then
                return here and try again.
              </Trans>
            </Text>
          </Alert>
          <Group justify='space-between'>
            <Button
              aria-label='mfa-send-verification'
              loading={sending}
              onClick={sendVerification}
            >
              <Trans>Send Verification Email</Trans>
            </Button>
            <Button
              aria-label='mfa-retry-setup'
              variant='outline'
              onClick={fetchSecret}
            >
              <Trans>Try Again</Trans>
            </Button>
          </Group>
        </Stack>
      </Wrapper>
    );
  }

  return (
    <Wrapper titleText={t`MFA Setup Required`} logOff>
      <QrRegistrationForm
        url={totpQr?.totp_url ?? ''}
        secret={totpQr?.secret ?? ''}
        value={value}
        setValue={setValue}
      />
      <Button
        disabled={!value}
        onClick={handleVerifyTotp(value, navigate, location)}
      >
        <Trans>Add TOTP</Trans>
      </Button>
    </Wrapper>
  );
}
