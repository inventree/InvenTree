import {
  ActionIcon,
  Anchor,
  Breadcrumbs,
  Group,
  Paper,
  Text
} from '@mantine/core';
import { IconMenu2 } from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';

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

  return (
    <Paper p="3" radius="xs">
      <Group spacing="xs">
        {navCallback && (
          <ActionIcon key="nav-action" onClick={navCallback}>
            <IconMenu2 />
          </ActionIcon>
        )}
        <Breadcrumbs key="breadcrumbs" separator=">">
          {breadcrumbs.map((breadcrumb, index) => {
            return (
              <Anchor
                key={index}
                onClick={() => breadcrumb.url && navigate(breadcrumb.url)}
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
