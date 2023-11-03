import { Trans, t } from '@lingui/macro';
import {
  ActionIcon,
  Anchor,
  Button,
  Divider,
  Group,
  HoverCard,
  Skeleton,
  Text,
  UnstyledButton
} from '@mantine/core';
import { IconLayoutSidebar } from '@tabler/icons-react';
import { useEffect, useState } from 'react';

import { menuItems } from '../../defaults/menuItems';
import { InvenTreeStyle } from '../../globalStyle';
import { useServerApiState } from '../../states/ApiState';
import { useLocalState } from '../../states/LocalState';
import { InvenTreeLogo } from '../items/InvenTreeLogo';
import { MenuLinks } from '../items/MenuLinks';

export function NavHoverMenu({
  openDrawer: openDrawer
}: {
  openDrawer: () => void;
}) {
  const { classes, theme } = InvenTreeStyle();
  const [hostKey, hostList] = useLocalState((state) => [
    state.hostKey,
    state.hostList
  ]);
  const [servername] = useServerApiState((state) => [state.server.instance]);
  const [instanceName, setInstanceName] = useState<string>();

  useEffect(() => {
    if (hostKey && hostList[hostKey]) {
      setInstanceName(hostList[hostKey]?.name);
    }
  }, [hostKey]);

  return (
    <HoverCard
      width={600}
      openDelay={300}
      position="bottom"
      shadow="md"
      withinPortal
    >
      <HoverCard.Target>
        <UnstyledButton onClick={() => openDrawer()}>
          <InvenTreeLogo />
        </UnstyledButton>
      </HoverCard.Target>

      <HoverCard.Dropdown sx={{ overflow: 'hidden' }}>
        <Group position="apart" px="md">
          <ActionIcon
            onClick={openDrawer}
            onMouseOver={openDrawer}
            title={t`Open Navigation`}
          >
            <IconLayoutSidebar />
          </ActionIcon>
          <Group spacing={'xs'}>
            {instanceName ? (
              instanceName
            ) : (
              <Skeleton height={20} width={40} radius={theme.defaultRadius} />
            )}{' '}
            |{' '}
            {servername ? (
              servername
            ) : (
              <Skeleton height={20} width={40} radius={theme.defaultRadius} />
            )}
          </Group>
          <Anchor href="#" fz="xs" onClick={openDrawer}>
            <Trans>View all</Trans>
          </Anchor>
        </Group>

        <Divider
          my="sm"
          mx="-md"
          color={theme.colorScheme === 'dark' ? 'dark.5' : 'gray.1'}
        />
        <MenuLinks links={menuItems} highlighted={true} />
        <div className={classes.headerDropdownFooter}>
          <Group position="apart">
            <div>
              <Text fw={500} fz="sm">
                <Trans>Get started</Trans>
              </Text>
              <Text size="xs" color="dimmed">
                <Trans>
                  Overview over high-level objects, functions and possible
                  usecases.
                </Trans>
              </Text>
            </div>
            <Button variant="default">
              <Trans>Get started</Trans>
            </Button>
          </Group>
        </div>
      </HoverCard.Dropdown>
    </HoverCard>
  );
}
