import { Trans } from '@lingui/macro';
import { Group } from '@mantine/core';
import { Placeholder } from '../../components/items/Placeholder';
import { StylishText } from '../../components/items/StylishText';

export default function Part() {
  return (
    <>
      <Group>
        <StylishText>
          <Trans>Part</Trans>
        </StylishText>
        <Placeholder />
      </Group>
    </>
  );
}
