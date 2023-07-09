import { Trans } from '@lingui/macro';
import {
  Anchor,
  Button,
  Divider,
  Group,
  HoverCard,
  SimpleGrid,
  Skeleton,
  Text,
  UnstyledButton
} from '@mantine/core';
import React, { useEffect, useState } from 'react';

import { useApiState } from '../../context/ApiState';
import { useLocalState } from '../../context/LocalState';
import { menuItems } from '../../defaults';
import { InvenTreeStyle } from '../../globalStyle';
import { DocTooltip } from '../items/DocTooltip';
import { InvenTreeLogo } from '../items/InvenTreeLogo';

export interface MenuLinkItem {
  title: string;
  description: string;
  detail?: string;
  link?: string;
  children?: React.ReactNode;
}

export function MegaHoverMenu() {
  const { classes, theme } = InvenTreeStyle();
  const [hostKey, hostList] = useLocalState((state) => [
    state.hostKey,
    state.hostList
  ]);
  const [servername] = useApiState((state) => [state.server.instance]);
  const [instanceName, setInstanceName] = useState<string>();

  useEffect(() => {
    if (hostKey && hostList[hostKey]) {
      setInstanceName(hostList[hostKey].name);
    }
  }, [hostKey]);

  return (
    <HoverCard width={600} position="bottom" shadow="md" withinPortal>
      <HoverCard.Target>
        <a href="#">
          <InvenTreeLogo />
        </a>
      </HoverCard.Target>

      <HoverCard.Dropdown sx={{ overflow: 'hidden' }}>
        <Group position="apart" px="md">
          <Anchor href="">
            <Text fw={500}>
              <Trans>Home</Trans>
            </Text>
          </Anchor>
          <Group spacing={'xs'}>
            {instanceName ? (
              instanceName
            ) : (
              <Skeleton height={20} width={40} radius={0} />
            )}{' '}
            |{' '}
            {servername ? (
              servername
            ) : (
              <Skeleton height={20} width={40} radius={0} />
            )}
          </Group>
          <Anchor href="#" fz="xs">
            <Trans>View all</Trans>
          </Anchor>
        </Group>

        <Divider
          my="sm"
          mx="-md"
          color={theme.colorScheme === 'dark' ? 'dark.5' : 'gray.1'}
        />
        <MenuLinks links={menuItems} />
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

function MenuLinks({ links }: { links: MenuLinkItem[] }) {
  const { classes } = InvenTreeStyle();

  let linksItems = links.map((item) => (
    <DocTooltip
      text={item.description}
      detail={item?.detail}
      link={item?.link}
      docchildren={item?.children}
    >
      <UnstyledButton className={classes.subLink} key={item.title}>
        <Text size="sm" fw={500}>
          {item.title}
        </Text>
      </UnstyledButton>
    </DocTooltip>
  ));
  return (
    <SimpleGrid cols={2} spacing={0}>
      {linksItems}
    </SimpleGrid>
  );
}
