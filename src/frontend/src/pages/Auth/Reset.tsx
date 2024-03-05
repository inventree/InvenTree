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
import { useNavigate } from 'react-router-dom';

import { LanguageContext } from '../../contexts/LanguageContext';
import { handleReset } from '../../functions/auth';

export default function Reset() {
  const simpleForm = useForm({ initialValues: { email: '' } });
  const navigate = useNavigate();

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
                placeholder="email@example.org"
                {...simpleForm.getInputProps('email')}
              />
            </Stack>
            <Button
              type="submit"
              onClick={() => handleReset(navigate, simpleForm.values)}
            >
              <Trans>Send mail</Trans>
            </Button>
          </Stack>
        </Container>
      </Center>
    </LanguageContext>
  );
}
