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
  subtitle,
  detail,
  breadcrumbs,
  actions
}: {
  title: string;
  subtitle?: string;
  detail?: ReactNode;
  breadcrumbs?: Breadcrumb[];
  actions?: ReactNode[];
}) {
  return (
    <Paper p="xs" radius="xs" shadow="xs">
      <Stack spacing="xs">
        <Group position="apart">
          <Group position="left">
            <Text size="xl">{title}</Text>
            {subtitle && <Text size="lg">{subtitle}</Text>}
          </Group>
          <Space />
          {actions && <Group position="right">{actions}</Group>}
        </Group>
        {breadcrumbs && <BreadcrumbList breadcrumbs={breadcrumbs} />}
        {detail}
      </Stack>
    </Paper>
  );
}
