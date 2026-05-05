import { Group, Paper, Space, Stack, Text } from '@mantine/core';
import { useHotkeys } from '@mantine/hooks';

import { StylishText } from '@lib/components/StylishText';
import { shortenString } from '@lib/functions/String';
import { Fragment, type ReactNode, useMemo } from 'react';
import { useUserSettingsState } from '../../states/SettingsStates';
import { ApiImage } from '../images/ApiImage';
import { type Breadcrumb, BreadcrumbList } from './BreadcrumbList';
import PageTitle from './PageTitle';

interface PageDetailInterface {
  title?: string;
  icon?: ReactNode;
  subtitle?: string;
  imageUrl?: string;
  badges?: ReactNode[];
  breadcrumbs?: Breadcrumb[];
  lastCrumb?: Breadcrumb[];
  thumbnailUrl?: string;
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
  badges,
  imageUrl,
  thumbnailUrl,
  breadcrumbs,
  lastCrumb: last_crumb,
  breadcrumbAction,
  actions,
  editAction,
  editEnabled
}: Readonly<PageDetailInterface>) {
  const userSettings = useUserSettingsState();
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

  const pageTitleString = useMemo(
    () =>
      shortenString({
        str: title,
        len: 50
      }),
    [title]
  );

  const description = useMemo(
    () =>
      shortenString({
        str: subtitle,
        len: 75
      }),
    [subtitle]
  );

  // breadcrumb caching
  const computedBreadcrumbs = useMemo(() => {
    if (userSettings.isSet('ENABLE_LAST_BREADCRUMB', false)) {
      return [...(breadcrumbs ?? []), ...(last_crumb ?? [])];
    } else {
      return breadcrumbs;
    }
  }, [breadcrumbs, last_crumb, userSettings]);

  return (
    <>
      <PageTitle title={pageTitleString} />
      <Stack gap='xs'>
        {computedBreadcrumbs && computedBreadcrumbs.length > 0 && (
          <BreadcrumbList
            navCallback={breadcrumbAction}
            breadcrumbs={computedBreadcrumbs}
          />
        )}
        <Paper p='xs' radius='xs' shadow='xs'>
          <Group
            justify='space-between'
            gap='xs'
            wrap='nowrap'
            align='flex-start'
          >
            <Group
              justify='space-between'
              wrap='nowrap'
              align='flex-start'
              style={{ flexGrow: 1 }}
            >
              <Group justify='start' wrap='nowrap' align='flex-start'>
                {imageUrl && (
                  <ApiImage
                    src={imageUrl}
                    thumbnail={thumbnailUrl}
                    radius='sm'
                    miw={42}
                    mah={42}
                    maw={42}
                    visibleFrom='sm'
                  />
                )}
                <Stack gap='xs'>
                  {title && <StylishText size='lg'>{title}</StylishText>}
                  {subtitle && (
                    <Group gap='xs'>
                      {icon}
                      <Text size='sm'>{description}</Text>
                    </Group>
                  )}
                </Stack>
              </Group>
              {badges && (
                <Group justify='flex-end' gap='xs' align='center'>
                  {badges?.map((badge, idx) => (
                    <Fragment key={idx}>{badge}</Fragment>
                  ))}
                  <Space w='md' />
                </Group>
              )}
            </Group>
            {actions && (
              <Group gap={5} justify='right' wrap='nowrap' align='flex-start'>
                {actions.map((action, idx) => (
                  <Fragment key={idx}>{action}</Fragment>
                ))}
              </Group>
            )}
          </Group>
        </Paper>
      </Stack>
    </>
  );
}
