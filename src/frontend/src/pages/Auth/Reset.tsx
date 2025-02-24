import { Trans, t } from '@lingui/macro';
import { Button, TextInput } from '@mantine/core';
import { useForm } from '@mantine/form';
import { useNavigate } from 'react-router-dom';
import { handleReset } from '../../functions/auth';
import { Wrapper } from './Layout';

export default function Reset() {
  const simpleForm = useForm({ initialValues: { email: '' } });
  const navigate = useNavigate();

  return (
    <Wrapper titleText={t`Reset Password`}>
      <TextInput
        required
        label={t`Email`}
        description={t`We will send you a link to login - if you are registered`}
        placeholder='email@example.org'
        {...simpleForm.getInputProps('email')}
      />
      <Button
        type='submit'
        onClick={() => handleReset(navigate, simpleForm.values)}
      >
        <Trans>Send Email</Trans>
      </Button>
    </Wrapper>
  );
}
