import { Trans, t } from '@lingui/macro';
import {
  Button,
  Center,
  Container,
  Stack,
  TextInput,
  Title
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { useNavigate } from 'react-router-dom';

import { api } from '../../App';
import { LanguageContext } from '../../contexts/LanguageContext';
import { ApiPaths, url } from '../../states/ApiState';

export default function Reset() {
  const simpleForm = useForm({ initialValues: { email: '' } });
  const navigate = useNavigate();

  function handleReset() {
    api
      .post(url(ApiPaths.user_reset), simpleForm.values, {
        headers: { Authorization: '' }
      })
      .then((val) => {
        if (val.status === 200) {
          notifications.show({
            title: t`Mail delivery successfull`,
            message: t`Check your inbox for a reset link. This only works if you have an account. Check in spam too.`,
            color: 'green',
            autoClose: false
          });
          navigate('/login');
        } else {
          notifications.show({
            title: t`Reset failed`,
            message: t`Check your your input and try again.`,
            color: 'red'
          });
        }
      });
  }

  return (
    <LanguageContext>
      <Center mih="100vh">
        <Container w="md" miw={425}>
          <Stack>
            <Title>
              <Trans>Reset password</Trans>
            </Title>
            <Stack>
              <TextInput
                required
                label={t`Email`}
                description={t`We will send you a link to login - if you are registered`}
                placeholder="code@mjmair.com"
                {...simpleForm.getInputProps('email')}
              />
            </Stack>
            <Button type="submit" onClick={handleReset}>
              <Trans>Send mail</Trans>
            </Button>
          </Stack>
        </Container>
      </Center>
    </LanguageContext>
  );
}
