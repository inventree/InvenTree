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
  UnstyledButton,
  useMantineColorScheme
} from '@mantine/core';
import { IconLayoutSidebar } from '@tabler/icons-react';
import { useEffect, useState } from 'react';

import { menuItems } from '../../defaults/menuItems';
import * as classes from '../../main.css';
import { useServerApiState } from '../../states/ApiState';
import { useLocalState } from '../../states/LocalState';
import { vars } from '../../theme';
import { InvenTreeLogo } from '../items/InvenTreeLogo';
import { MenuLinks } from '../items/MenuLinks';

const onlyItems = Object.values(menuItems);

export function NavHoverMenu({
  openDrawer: openDrawer
}: {
  openDrawer: () => void;
}) {
  const [hostKey, hostList] = useLocalState((state) => [
    state.hostKey,
    state.hostList
  ]);
  const [servername] = useServerApiState((state) => [state.server.instance]);
  const [instanceName, setInstanceName] = useState<string>();
  const { colorScheme } = useMantineColorScheme();

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
        <UnstyledButton onClick={() => openDrawer()} aria-label="Homenav">
          <InvenTreeLogo />
        </UnstyledButton>
      </HoverCard.Target>

      <HoverCard.Dropdown style={{ overflow: 'hidden' }}>
        <Group justify="space-between" px="md">
          <ActionIcon
            onClick={openDrawer}
            onMouseOver={openDrawer}
            title={t`Open Navigation`}
            variant="default"
          >
            <IconLayoutSidebar />
          </ActionIcon>
          <Group gap={'xs'}>
            {instanceName ? (
              instanceName
            ) : (
              <Skeleton height={20} width={40} radius={vars.radiusDefault} />
            )}{' '}
            |{' '}
            {servername ? (
              servername
            ) : (
              <Skeleton height={20} width={40} radius={vars.radiusDefault} />
            )}
          </Group>
          <Anchor href="#" fz="xs" onClick={openDrawer}>
            <Trans>View all</Trans>
          </Anchor>
        </Group>

        <Divider
          my="sm"
          mx="-md"
          color={
            colorScheme === 'dark' ? vars.colors.dark[5] : vars.colors.gray[1]
          }
        />
        <MenuLinks links={onlyItems} highlighted={true} />
        <div className={classes.headerDropdownFooter}>
          <Group justify="space-between">
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
