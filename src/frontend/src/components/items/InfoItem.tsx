import { Trans } from '@lingui/macro';
import { Flex, Group, Text } from '@mantine/core';

import { YesNoButton } from './YesNoButton';

export function InfoItem({
  name,
  children,
  type,
  value
}: {
  name: string;
  children?: React.ReactNode;
  type?: 'text' | 'boolean';
  value?: any;
}) {
  return (
    <Group position="apart">
      <Text fz="sm" fw={700}>
        {name}:
      </Text>
      <Flex>
        {children}
        {value !== undefined && type === 'text' ? (
          <Text>{value || <Trans>None</Trans>}</Text>
        ) : type === 'boolean' ? (
          <YesNoButton value={value || false} />
        ) : (
          ''
        )}
      </Flex>
    </Group>
  );
}
