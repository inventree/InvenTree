import { Group, Paper, Space, Stack, Text } from '@mantine/core';
import { ReactNode } from 'react';

import { Breadcrumb, BreadcrumbList } from './BreadcrumbList';

/**
 * Construct a "standard" page detail for common display between pages.
 *
 * @param breadcrumbs - The breadcrumbs to display (optional)
 * @param
 */
export function PageDetail({
  title,
  detail,
  breadcrumbs,
  actions
}: {
  title: string;
  detail: ReactNode;
  breadcrumbs?: Breadcrumb[];
  actions?: ReactNode[];
}) {
  return (
    <Paper p="xs" radius="xs">
      <Stack spacing="xs">
        <Group position="apart">
          <Text size="lg">{title}</Text>
          <Space />
          {actions && <Group position="right">{actions}</Group>}
        </Group>
        {breadcrumbs && <BreadcrumbList breadcrumbs={breadcrumbs} />}
        {detail}
      </Stack>
    </Paper>
  );
}
