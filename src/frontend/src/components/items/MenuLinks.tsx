import { SimpleGrid, Text, UnstyledButton } from '@mantine/core';
import React from 'react';

import { InvenTreeStyle } from '../../globalStyle';
import { DocTooltip } from './DocTooltip';

export interface MenuLinkItem {
  id: string;
  title: string | JSX.Element;
  description: string | JSX.Element;
  detail?: string | JSX.Element;
  link?: string;
  children?: React.ReactNode;
}

export function MenuLinks({ links }: { links: MenuLinkItem[] }) {
  const { classes } = InvenTreeStyle();

  let linksItems = links.map((item) => (
    <DocTooltip
      key={item.id}
      text={item.description}
      detail={item?.detail}
      link={item?.link}
      docchildren={item?.children}
    >
      <UnstyledButton className={classes.subLink} key={item.id}>
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
