import { SimpleGrid, Text, UnstyledButton } from '@mantine/core';
import React from 'react';

import { InvenTreeStyle } from '../../globalStyle';
import { DocTooltip } from './DocTooltip';

export interface MenuLinkItem {
  title: string;
  description: string;
  detail?: string;
  link?: string;
  children?: React.ReactNode;
}

export function MenuLinks({ links }: { links: MenuLinkItem[] }) {
  const { classes } = InvenTreeStyle();

  let linksItems = links.map((item) => (
    <DocTooltip
      key={item.title}
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
