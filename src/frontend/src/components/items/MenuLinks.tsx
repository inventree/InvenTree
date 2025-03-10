import {
  Anchor,
  Divider,
  Group,
  SimpleGrid,
  Stack,
  Text,
  Tooltip,
  UnstyledButton
} from '@mantine/core';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { InvenTreeIcon, type InvenTreeIconType } from '../../functions/icons';
import { navigateToLink } from '../../functions/navigation';
import { StylishText } from './StylishText';

export interface MenuLinkItem {
  id: string;
  title: string | JSX.Element;
  description?: string;
  icon?: InvenTreeIconType;
  action?: () => void;
  link?: string;
  external?: boolean;
  hidden?: boolean;
}

export function MenuLinks({
  title,
  links,
  beforeClick
}: Readonly<{
  title: string;
  links: MenuLinkItem[];
  beforeClick?: () => void;
}>) {
  const navigate = useNavigate();

  // Filter out any hidden links
  const visibleLinks = useMemo(
    () => links.filter((item) => !item.hidden),
    [links]
  );

  if (visibleLinks.length == 0) {
    return null;
  }

  return (
    <>
      <Stack gap='xs'>
        <Divider />
        <StylishText size='md'>{title}</StylishText>
        <Divider />
        <SimpleGrid
          cols={{ base: 1, '400px': 2 }}
          type='container'
          spacing={0}
          p={3}
        >
          {visibleLinks.map((item) => (
            <Tooltip
              key={`menu-link-tooltip-${item.id}`}
              label={item.description}
              hidden={!item.description}
            >
              {item.link && item.external ? (
                <Anchor href={item.link}>
                  <Group wrap='nowrap'>
                    {item.external && (
                      <InvenTreeIcon
                        icon={item.icon ?? 'link'}
                        iconProps={{ size: '14' }}
                      />
                    )}
                    <Text fw={500} p={5}>
                      {item.title}
                    </Text>
                  </Group>
                </Anchor>
              ) : (
                <UnstyledButton
                  onClick={(event) => {
                    if (item.link) {
                      beforeClick?.();
                      navigateToLink(item.link, navigate, event);
                    } else if (item.action) {
                      beforeClick?.();
                      item.action();
                    }
                  }}
                >
                  <Group wrap='nowrap'>
                    {item.icon && (
                      <InvenTreeIcon
                        icon={item.icon}
                        iconProps={{ size: '14' }}
                      />
                    )}
                    <Text fw={500} p={5}>
                      {item.title}
                    </Text>
                  </Group>
                </UnstyledButton>
              )}
            </Tooltip>
          ))}
        </SimpleGrid>
      </Stack>
    </>
  );
}
