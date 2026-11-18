import { ActionIcon, Anchor, Breadcrumbs, Group, Text } from '@mantine/core';
import { IconMenu2 } from '@tabler/icons-react';
import { useMemo } from 'react';
import { Link } from 'react-router-dom';

import { identifierString } from '@lib/functions/Conversion';

export type Breadcrumb = {
  icon?: React.ReactNode;
  name: string;
  url: string;
};

/**
 * Construct a breadcrumb list, with integrated navigation.
 */
export function BreadcrumbList({
  breadcrumbs,
  navCallback
}: Readonly<{
  breadcrumbs: Breadcrumb[];
  navCallback?: () => void;
}>) {
  const elements = useMemo(() => {
    // Limit to 7 active elements
    if (breadcrumbs.length > 7) {
      return [
        ...breadcrumbs.slice(0, 3),
        { name: '...', url: '#' },
        ...breadcrumbs.slice(-3)
      ];
    } else {
      return breadcrumbs;
    }
  }, [breadcrumbs]);

  return (
    <Group
      gap='xs'
      wrap='nowrap'
      align='center'
      style={{ flex: 1, minWidth: 0 }}
    >
      {navCallback && (
        <ActionIcon
          key='nav-breadcrumb-action'
          aria-label='nav-breadcrumb-action'
          onClick={navCallback}
          variant='transparent'
        >
          <IconMenu2 />
        </ActionIcon>
      )}
      <Breadcrumbs key='breadcrumbs' separator='>'>
        {elements.map((breadcrumb, index) => {
          const content = (
            <Group gap={4} align='center'>
              {breadcrumb.icon}
              <Text size='sm'>{breadcrumb.name}</Text>
            </Group>
          );
          const ariaLabel = `breadcrumb-${index}-${identifierString(
            breadcrumb.name
          )}`;

          if (breadcrumb.url === '#') {
            return (
              <Group
                key={`${index}-${breadcrumb.name}`}
                gap={4}
                align='center'
                aria-label={ariaLabel}
              >
                {breadcrumb.icon}
                <Text size='sm'>{breadcrumb.name}</Text>
              </Group>
            );
          }

          return (
            <Anchor
              key={`${index}-${breadcrumb.name}`}
              component={Link}
              to={breadcrumb.url}
              aria-label={ariaLabel}
            >
              {content}
            </Anchor>
          );
        })}
      </Breadcrumbs>
    </Group>
  );
}
