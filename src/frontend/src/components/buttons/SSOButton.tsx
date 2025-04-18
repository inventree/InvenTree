import { Button, Tooltip } from '@mantine/core';
import {
  IconBrandAzure,
  IconBrandBitbucket,
  IconBrandDiscord,
  IconBrandFacebook,
  IconBrandFlickr,
  IconBrandGithub,
  IconBrandGitlab,
  IconBrandGoogle,
  IconBrandReddit,
  IconBrandTwitch,
  IconBrandTwitter,
  IconLogin
} from '@tabler/icons-react';

import type { AuthProvider } from '@lib/types/Auth';
import { t } from '@lingui/core/macro';
import { ProviderLogin } from '../../functions/auth';

const brandIcons: { [key: string]: JSX.Element } = {
  google: <IconBrandGoogle />,
  github: <IconBrandGithub />,
  facebook: <IconBrandFacebook />,
  discord: <IconBrandDiscord />,
  twitter: <IconBrandTwitter />,
  bitbucket: <IconBrandBitbucket />,
  flickr: <IconBrandFlickr />,
  gitlab: <IconBrandGitlab />,
  reddit: <IconBrandReddit />,
  twitch: <IconBrandTwitch />,
  microsoft: <IconBrandAzure />
};

export function SsoButton({ provider }: Readonly<{ provider: AuthProvider }>) {
  return (
    <Tooltip
      label={t`You will be redirected to the provider for further actions.`}
    >
      <Button
        leftSection={getBrandIcon(provider)}
        radius='xl'
        component='a'
        onClick={() => ProviderLogin(provider)}
      >
        {provider.name}
      </Button>
    </Tooltip>
  );
}
function getBrandIcon(provider: AuthProvider) {
  return brandIcons[provider.id] || <IconLogin />;
}
