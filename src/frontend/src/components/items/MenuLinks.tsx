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
  highlight?: boolean;
}

export function MenuLinks({
  links,
  highlighted
}: {
  links: MenuLinkItem[];
  highlighted?: boolean;
}) {
  const { classes } = InvenTreeStyle();
  highlighted = highlighted || false;

  const filteredLinks = links.filter(
    (item) => !highlighted || item.highlight === true
  );
  let linksItems = filteredLinks.map((item) => (
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
