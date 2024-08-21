import { Trans, t } from '@lingui/macro';
import {
  Divider,
  Flex,
  Paper,
  SimpleGrid,
  Stack,
  Text,
  Title
} from '@mantine/core';
import { IconHome } from '@tabler/icons-react';

import { ActionButton } from '../buttons/ActionButton';
import { PlaceholderPill } from '../items/Placeholder';

export const QuickAction = ({
  navigate,
  ml = 'sm'
}: {
  navigate?: any;
  ml?: string;
}) => {
  return (
    <Stack gap={'xs'} ml={ml}>
      <Title order={5}>
        <Trans>Quick Actions</Trans>
      </Title>
      <Flex align={'flex-end'}>
        {navigate ? (
          <>
            <ActionButton
              icon={<IconHome />}
              color="blue"
              size="lg"
              radius="sm"
              variant="filled"
              tooltip={t`Go to Home`}
              onClick={() => navigate('home')}
            />
            <Divider orientation="vertical" mx="md" />
          </>
        ) : null}
        <SimpleGrid cols={3}>
          <Paper shadow="xs" p="sm" withBorder>
            <Text>
              <Trans>Add a new user</Trans>
            </Text>
          </Paper>

          <Paper shadow="xs" p="sm" withBorder>
            <PlaceholderPill />
          </Paper>

          <Paper shadow="xs" p="sm" withBorder>
            <PlaceholderPill />
          </Paper>
        </SimpleGrid>
      </Flex>
    </Stack>
  );
};
