import { Anchor, Breadcrumbs, Paper, Text } from '@mantine/core';
import { useNavigate } from 'react-router-dom';

export type Breadcrumb = {
  name: string;
  url: string;
};

/**
 * Construct a breadcrumb list, with integrated navigation.
 */
export function BreadcrumbList({ breadcrumbs }: { breadcrumbs: Breadcrumb[] }) {
  const navigate = useNavigate();

  return (
    <Paper p="3" radius="xs">
      <Breadcrumbs>
        {breadcrumbs.map((breadcrumb, index) => {
          return (
            <Anchor
              key={`breadcrumb-${index}`}
              onClick={() => breadcrumb.url && navigate(breadcrumb.url)}
            >
              <Text size="sm">{breadcrumb.name}</Text>
            </Anchor>
          );
        })}
      </Breadcrumbs>
    </Paper>
  );
}
