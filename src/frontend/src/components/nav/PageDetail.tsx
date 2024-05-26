import { Group, Paper, Space, Stack, Text } from '@mantine/core';
import { Fragment, ReactNode } from 'react';

import { ApiImage } from '../images/ApiImage';
import { StylishText } from '../items/StylishText';
import { Breadcrumb, BreadcrumbList } from './BreadcrumbList';

interface PageDetailInterface {
  title?: string;
  subtitle?: string;
  imageUrl?: string;
  detail?: ReactNode;
  badges?: ReactNode[];
  breadcrumbs?: Breadcrumb[];
  breadcrumbAction?: () => void;
  actions?: ReactNode[];
}

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
  badges,
  imageUrl,
  breadcrumbs,
  breadcrumbAction,
  actions
}: Readonly<PageDetailInterface>) {
  return (
    <Stack gap="xs">
      {breadcrumbs && breadcrumbs.length > 0 && (
        <BreadcrumbList
          navCallback={breadcrumbAction}
          breadcrumbs={breadcrumbs}
        />
      )}
      <Paper p="xs" radius="xs" shadow="xs">
        <Stack gap="xs">
          <Group justify="space-between" wrap="nowrap">
            <Group justify="left" wrap="nowrap">
              {imageUrl && (
                <ApiImage src={imageUrl} radius="sm" h={64} w={64} />
              )}
              <Stack gap="xs">
                {title && <StylishText size="lg">{title}</StylishText>}
                {subtitle && (
                  <Text size="md" truncate>
                    {subtitle}
                  </Text>
                )}
              </Stack>
            </Group>
            <Space />
            {detail}
            <Group justify="right" gap="xs" wrap="nowrap">
              {badges?.map((badge, idx) => (
                <Fragment key={idx}>{badge}</Fragment>
              ))}
            </Group>
            <Space />
            {actions && (
              <Group gap={5} justify="right">
                {actions.map((action, idx) => (
                  <Fragment key={idx}>{action}</Fragment>
                ))}
              </Group>
            )}
          </Group>
        </Stack>
      </Paper>
    </Stack>
  );
}
