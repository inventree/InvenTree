import { Button } from '@mantine/core';
import {
  IconBrandGithub,
  IconBrandGoogle,
  IconLogin
} from '@tabler/icons-react';

import { Provider } from '../../states/states';

export function SooButton({ provider }: { provider: Provider }) {
  let icon = <IconLogin />;
  if (provider.id === 'google') {
    icon = <IconBrandGoogle />;
  } else if (provider.id === 'github') {
    icon = <IconBrandGithub />;
  }
  return (
    <Button leftIcon={icon} radius="xl" component="a" href={provider.connect}>
      {provider.display_name}{' '}
    </Button>
  );
}
