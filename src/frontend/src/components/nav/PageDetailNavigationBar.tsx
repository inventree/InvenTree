import { Group, Paper } from '@mantine/core';

import type { DetailNavigationState } from '../../hooks/UseDetailNavigation';
import { type Breadcrumb, BreadcrumbList } from './BreadcrumbList';
import { DetailNavigation } from './DetailNavigation';

export function PageDetailNavigationBar({
  breadcrumbs,
  breadcrumbAction,
  detailNavigation
}: Readonly<{
  breadcrumbs: Breadcrumb[];
  breadcrumbAction?: () => void;
  detailNavigation: DetailNavigationState;
}>) {
  const hasDetailNavigation = Boolean(
    detailNavigation.previous ||
      detailNavigation.next ||
      detailNavigation.position ||
      detailNavigation.isLoading
  );

  if (breadcrumbs.length === 0 && !hasDetailNavigation) {
    return null;
  }

  return (
    <Paper p='7' radius='xs' shadow='xs' data-testid='breadcrumb-list'>
      <Group gap='xs' justify='space-between' align='center' wrap='nowrap'>
        <BreadcrumbList
          navCallback={breadcrumbAction}
          breadcrumbs={breadcrumbs}
        />
        {hasDetailNavigation && (
          <DetailNavigation navigation={detailNavigation} />
        )}
      </Group>
    </Paper>
  );
}
