import { Trans, t } from '@lingui/macro';
import { Anchor, Text } from '@mantine/core';
import { useNavigate } from 'react-router-dom';
import { RegistrationForm } from '../../components/forms/AuthenticationForm';
import {} from '../../functions/auth';
import { Wrapper } from './Layout';

export default function Register() {
  const navigate = useNavigate();

  return (
    <Wrapper titleText={t`Register`} smallPadding>
      <RegistrationForm />
      <Text ta='center' size={'xs'} mt={'md'}>
        <Anchor
          component='button'
          type='button'
          c='dimmed'
          size='xs'
          onClick={() => navigate('/login')}
        >
          <Trans>Go back to login</Trans>
        </Anchor>
      </Text>
    </Wrapper>
  );
}
