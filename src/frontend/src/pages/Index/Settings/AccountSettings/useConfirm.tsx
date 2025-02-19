import { Trans, t } from '@lingui/macro';
import { Button, Group, Modal, Stack, TextInput } from '@mantine/core';
import { useState } from 'react';

/* Adapted from https://daveteu.medium.com/react-custom-confirmation-box-458cceba3f7b */
const createPromise = () => {
  let resolver: any;
  return [
    new Promise((resolve) => {
      resolver = resolve;
    }),
    resolver
  ];
};

/* Adapted from https://daveteu.medium.com/react-custom-confirmation-box-458cceba3f7b */
export const useConfirm = () => {
  const [open, setOpen] = useState(false);
  const [resolver, setResolver] = useState<((status: boolean) => void) | null>(
    null
  );
  const [label, setLabel] = useState('');

  const getConfirmation = async (text: string) => {
    setLabel(text);
    setOpen(true);
    const [promise, resolve] = await createPromise();

    setResolver(resolve);
    return promise;
  };

  const onClick = async (status: boolean) => {
    setOpen(false);
    if (resolver) {
      resolver(status);
    }
  };

  const Confirmation = () => (
    <Modal opened={open} onClose={() => setOpen(false)}>
      {label}
      <Button onClick={() => onClick(false)}> Cancel </Button>
      <Button onClick={() => onClick(true)}> OK </Button>
    </Modal>
  );

  return [getConfirmation, Confirmation];
};

type InputProps = {
  label: string;
  name: string;
  description: string;
};
export const useReauth = (): [
  (props: InputProps) => Promise<[string, boolean]>,
  () => JSX.Element
] => {
  const [inputProps, setInputProps] = useState<InputProps>({
    label: '',
    name: '',
    description: ''
  });

  const [value, setValue] = useState('');
  const [open, setOpen] = useState(false);
  const [resolver, setResolver] = useState<{
    resolve: (result: string, positive: boolean) => void;
  } | null>(null);

  const getReauthText = async (props: InputProps) => {
    setInputProps(props);
    setOpen(true);
    const [promise, resolve] = await createPromise();

    setResolver({ resolve });
    return promise;
  };

  const onClick = async (result: string, positive: boolean) => {
    setOpen(false);
    if (resolver) {
      resolver.resolve(result, positive);
    }
  };

  const ReauthModal = () => (
    <Modal
      opened={open}
      onClose={() => setOpen(false)}
      title={t`Reauthentication`}
    >
      <Stack>
        <TextInput
          required
          label={inputProps.label}
          name={inputProps.name}
          description={inputProps.description}
          value={value}
          onChange={(event) => setValue(event.currentTarget.value)}
        />
        <Group justify='space-between'>
          <Button onClick={() => onClick('', false)} color='red'>
            <Trans>Cancel</Trans>
          </Button>
          <Button onClick={() => onClick(value, true)}>
            <Trans>OK</Trans>
          </Button>
        </Group>
      </Stack>
    </Modal>
  );

  return [getReauthText, ReauthModal];
};
