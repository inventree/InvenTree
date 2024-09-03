import { Group, Paper, Space, Stack, Text } from '@mantine/core';
import { useHotkeys } from '@mantine/hooks';
import { Fragment, ReactNode } from 'react';

import { ApiImage } from '../images/ApiImage';
import { StylishText } from '../items/StylishText';
import { Breadcrumb, BreadcrumbList } from './BreadcrumbList';

interface PageDetailInterface {
  title?: string;
  icon?: ReactNode;
  subtitle?: string;
  imageUrl?: string;
  detail?: ReactNode;
  badges?: ReactNode[];
  breadcrumbs?: Breadcrumb[];
  breadcrumbAction?: () => void;
  actions?: ReactNode[];
  editAction?: () => void;
  editEnabled?: boolean;
}

/**
 * Construct a "standard" page detail for common display between pages.
 *
 * @param breadcrumbs - The breadcrumbs to display (optional)
 * @param
 */
export function PageDetail({
  title,
  icon,
  subtitle,
  detail,
  badges,
  imageUrl,
  breadcrumbs,
  breadcrumbAction,
  actions,
  editAction,
  editEnabled
}: Readonly<PageDetailInterface>) {
  useHotkeys([
    [
      'mod+E',
      () => {
        if (editEnabled ?? true) {
          editAction?.();
        }
      }
    ]
  ]);

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
                  <Group gap="xs">
                    {icon}
                    <Text size="md" truncate>
                      {subtitle}
                    </Text>
                  </Group>
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
