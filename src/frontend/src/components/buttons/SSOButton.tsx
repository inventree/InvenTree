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
  function login() {
    window.location.href = provider.login;
  }

  return (
    <Tooltip
      label={
        provider.login
          ? t`You will be redirected to the provider for further actions.`
          : t`This provider is not full set up.`
      }
    >
      <Button
        leftSection={getBrandIcon(provider)}
        radius='xl'
        component='a'
        onClick={login}
        disabled={!provider.login}
      >
        {provider.display_name}
      </Button>
    </Tooltip>
  );
}
function getBrandIcon(provider: Provider) {
  return brandIcons[provider.id] || <IconLogin />;
}
