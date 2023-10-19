import { Group, Paper, Space, Stack, Text } from '@mantine/core';
import { ReactNode } from 'react';

import { StylishText } from '../items/StylishText';
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
  title?: string;
  subtitle?: string;
  detail?: ReactNode;
  breadcrumbs?: Breadcrumb[];
  actions?: ReactNode[];
}) {
  return (
    <Stack spacing="xs">
      {breadcrumbs && breadcrumbs.length > 0 && (
        <Paper p="xs" radius="xs" shadow="xs">
          <BreadcrumbList breadcrumbs={breadcrumbs} />
        </Paper>
      )}
      <Paper p="xs" radius="xs" shadow="xs">
        <Stack spacing="xs">
          <Group position="apart">
            <Group position="left">
              <Stack spacing="xs">
                {title && <StylishText size="xl">{title}</StylishText>}
                {subtitle && <Text size="lg">{subtitle}</Text>}
                {detail}
              </Stack>
            </Group>
            <Space />
            {actions && (
              <Group spacing={5} position="right">
                {actions}
              </Group>
            )}
          </Group>
        </Stack>
      </Paper>
    </Stack>
  );
}
