import { Trans } from '@lingui/macro';
import { SimpleGrid, Title } from '@mantine/core';

import { ColorToggle } from '../items/ColorToggle';
import { LanguageSelect } from '../items/LanguageSelect';

export default function DisplayWidget() {
  return (
    <span>
      <Title order={5}>
        <Trans>Display Settings</Trans>
      </Title>
      <SimpleGrid cols={2} spacing={0}>
        <div>
          <Trans>Color Mode</Trans>
        </div>
        <div>
          <ColorToggle />
        </div>
        <div>
          <Trans>Language</Trans>
        </div>
        <div>
          <LanguageSelect width={140} />
        </div>
      </SimpleGrid>
    </span>
  );
}
