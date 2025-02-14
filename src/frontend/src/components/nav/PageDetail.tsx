import { Group, Paper, SimpleGrid, Stack, Text } from '@mantine/core';
import { useHotkeys } from '@mantine/hooks';

import { Fragment, type ReactNode, useMemo } from 'react';
import { shortenString } from '../../functions/tables';
import { useUserSettingsState } from '../../states/SettingsState';
import { ApiImage } from '../images/ApiImage';
import { StylishText } from '../items/StylishText';
import { type Breadcrumb, BreadcrumbList } from './BreadcrumbList';
import PageTitle from './PageTitle';

interface PageDetailInterface {
  title?: string;
  icon?: ReactNode;
  subtitle?: string;
  imageUrl?: string;
  detail?: ReactNode;
  badges?: ReactNode[];
  breadcrumbs?: Breadcrumb[];
  lastCrumb?: Breadcrumb[];
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

  const maxCols = useMemo(() => {
    let cols = 1;

    if (!!detail) {
      cols++;
    }

    if (!!badges) {
      cols++;
    }

    return cols;
  }, [detail, badges]);

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
            <SimpleGrid
              cols={{
                base: 1,
                md: Math.min(2, maxCols),
                lg: Math.min(3, maxCols)
              }}
            >
              <Group justify='left' wrap='nowrap'>
                {imageUrl && (
                  <ApiImage
                    src={imageUrl}
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
              {detail && <div>{detail}</div>}
              {badges && (
                <Group
                  justify='center'
                  gap='xs'
                  align='flex-start'
                  wrap='nowrap'
                >
                  {badges?.map((badge, idx) => (
                    <Fragment key={idx}>{badge}</Fragment>
                  ))}
                </Group>
              )}
            </SimpleGrid>
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
