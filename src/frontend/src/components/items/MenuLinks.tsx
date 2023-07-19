import { SimpleGrid, Text, UnstyledButton } from '@mantine/core';
import React from 'react';

import { InvenTreeStyle } from '../../globalStyle';
import { DocTooltip } from './DocTooltip';

export interface MenuLinkItem {
  id: string;
  title: string | JSX.Element;
  description?: string | JSX.Element;
  detail?: string | JSX.Element;
  link?: string;
  children?: React.ReactNode;
  highlight?: boolean;
}

function ConditionalDocTooltip({
  item,
  children
}: {
  item: MenuLinkItem;
  children: React.ReactNode;
}) {
  if (item.description !== undefined) {
    return (
      <DocTooltip
        key={item.id}
        text={item.description}
        detail={item?.detail}
        link={item.link}
        docchildren={item?.children}
      >
        {children}
      </DocTooltip>
    );
  }
  return <>{children}</>;
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
  return (
    <SimpleGrid cols={2} spacing={0}>
      {filteredLinks.map((item) => (
        <ConditionalDocTooltip item={item}>
          <UnstyledButton className={classes.subLink} key={item.id}>
            <Text size="sm" fw={500}>
              {item.title}
            </Text>
          </UnstyledButton>
        </ConditionalDocTooltip>
      ))}
    </SimpleGrid>
  );
}
