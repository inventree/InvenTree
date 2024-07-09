import {
  ActionIcon,
  Anchor,
  Breadcrumbs,
  Group,
  Paper,
  Text
} from '@mantine/core';
import { IconMenu2 } from '@tabler/icons-react';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { identifierString } from '../../functions/conversion';
import { navigateToLink } from '../../functions/navigation';

export type Breadcrumb = {
  name: string;
  url: string;
};

/**
 * Construct a breadcrumb list, with integrated navigation.
 */
export function BreadcrumbList({
  breadcrumbs,
  navCallback
}: {
  breadcrumbs: Breadcrumb[];
  navCallback?: () => void;
}) {
  const navigate = useNavigate();

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
    <Paper p="7" radius="xs" shadow="xs">
      <Group gap="xs">
        {navCallback && (
          <ActionIcon
            key="nav-breadcrumb-action"
            aria-label="nav-breadcrumb-action"
            onClick={navCallback}
            variant="transparent"
          >
            <IconMenu2 />
          </ActionIcon>
        )}
        <Breadcrumbs key="breadcrumbs" separator=">">
          {elements.map((breadcrumb, index) => {
            return (
              <Anchor
                key={index}
                aria-label={`breadcrumb-${index}-${identifierString(
                  breadcrumb.name
                )}`}
                onClick={(event: any) =>
                  breadcrumb.url &&
                  navigateToLink(breadcrumb.url, navigate, event)
                }
              >
                <Text size="sm">{breadcrumb.name}</Text>
              </Anchor>
            );
          })}
        </Breadcrumbs>
      </Group>
    </Paper>
  );
}
