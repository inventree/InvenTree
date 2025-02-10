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

import { t } from '@lingui/macro';
import { ProviderLogin } from '../../functions/auth';
import type { Provider } from '../../states/states';

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

export function SsoButton({ provider }: Readonly<{ provider: Provider }>) {
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
function getBrandIcon(provider: Provider) {
  return brandIcons[provider.id] || <IconLogin />;
}
