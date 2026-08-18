import { ActionIcon, Group, Paper, Space, Stack, Text } from '@mantine/core';

import { StylishText } from '@lib/components/StylishText';
import { useInvenTreeHotkeys } from '@lib/functions/Events';
import { getDetailUrl, navigateToLink } from '@lib/functions/Navigation';
import { shortenString } from '@lib/functions/String';
import { t } from '@lingui/core/macro';
import { IconChevronLeft, IconChevronRight } from '@tabler/icons-react';
import { Fragment, type ReactNode, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { usePluginUIFeature } from '../../hooks/UsePluginUIFeature';
import { useUserSettingsState } from '../../states/SettingsStates';
import {
  setTableNavigationContext,
  useTableNavigationState
} from '../../states/TableNavigationState';
import PrimaryActionButton from '../buttons/PrimaryActionButton';
import { ApiImage } from '../images/ApiImage';
import { ApiIcon } from '../items/ApiIcon';
import type { PrimaryActionUIFeature } from '../plugins/PluginUIFeatureTypes';
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
  const navigate = useNavigate();
  const location = useLocation();

  const navigationState = useTableNavigationState();
  const navigationContext = navigationState.context;

  useInvenTreeHotkeys([
    [
      'mod+E',
      t`Edit`,
      (event) => {
        if (event.repeat) {
          return;
        }
        if (editEnabled ?? true) {
          editAction?.();
        }
      }
    ]
  ]);
  useActionHotkeys(actions);

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

  const extraActions = usePluginUIFeature<PrimaryActionUIFeature>({
    featureType: 'primary_action',
    context: { location: location.pathname }
  });

  // action caching
  const computedActions = useMemo(() => {
    const extraActionArray: ReactNode[] = extraActions.map((action) => {
      const { options: opts, func } = action;
      const { title, icon, context, options } = opts;

      const click = () => {
        const url = options?.url;
        if (url) {
          navigate(url);
        } else if (func) {
          func(context);
        }
      };

      return (
        <PrimaryActionButton
          title={title}
          leftSection={<ApiIcon name={icon as string} />}
          color={options?.color}
          onClick={click}
          key={title}
        />
      );
    });
    return [...(extraActionArray ?? []), ...(actions ?? [])];
  }, [extraActions, actions]);

  // previous / next navigation between the records in the list the user came from
  const detailNavigation = useMemo(() => {
    if (!navigationContext) return null;

    const index = navigationContext.records.findIndex(
      (record) => String(record) === String(navigationContext.current)
    );

    if (index < 0) return null;

    const previous = index > 0 ? navigationContext.records[index - 1] : null;
    const next =
      index < navigationContext.records.length - 1
        ? navigationContext.records[index + 1]
        : null;

    if (previous == null && next == null) return null;

    const goTo = (pk: number | string, event: any) => {
      const url = getDetailUrl(navigationContext.model, pk);

      if (url) {
        navigateToLink(url, navigate, event);
        setTableNavigationContext({ ...navigationContext, current: pk });
      }
    };

    return (
      <Group gap={2} justify='right' wrap='nowrap' align='center'>
        <ActionIcon
          variant='subtle'
          disabled={previous == null}
          title={t`Previous`}
          aria-label='previous-object'
          onClick={(event) => {
            if (previous != null) {
              goTo(previous, event);
            }
          }}
        >
          <IconChevronLeft />
        </ActionIcon>
        <ActionIcon
          variant='subtle'
          disabled={next == null}
          title={t`Next`}
          aria-label='next-object'
          onClick={(event) => {
            if (next != null) {
              goTo(next, event);
            }
          }}
        >
          <IconChevronRight />
        </ActionIcon>
      </Group>
    );
  }, [navigationContext, navigate]);

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
            {detailNavigation}
            {computedActions && (
              <Group gap={5} justify='right' wrap='nowrap' align='flex-start'>
                {computedActions.map((action, idx) => (
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

function useActionHotkeys(actions: ReactNode[] = []) {
  const hotkeys = useMemo(() => extractHotkeys(actions), [actions]);

  useInvenTreeHotkeys(
    hotkeys.map(({ hotkey, onClick, name }) => [
      hotkey,
      name,
      (event) => {
        if (event.repeat) {
          return;
        }
        onClick();
      }
    ])
  );
}

function extractHotkeys(actions: ReactNode[]) {
  const calcActions = actions
    .filter(
      (action) =>
        action &&
        typeof action === 'object' &&
        'hotkey' in action &&
        action.hotkey
    )
    .map((action: any) => {
      return {
        hotkey: action?.hotkey,
        name: action?.name,
        onClick: action?.onClick
      };
    })
    .filter((action) => action !== null);

  let primaryActionHotkeyAdded = false;
  // now iterate over the actions to extract more possible hotkeys
  actions.forEach((action: any) => {
    const typeName = action?.type?.name;

    // dropdowns - nested actions
    if (typeName === 'ActionDropdown' || typeName === 'OptionsActionDropdown') {
      const dropdownActions = action?.props?.actions as any[];
      dropdownActions.forEach((dropdownAction: any) => {
        if (dropdownAction.hotkey) {
          calcActions.push({
            hotkey: dropdownAction.hotkey,
            name: dropdownAction.name,
            onClick: dropdownAction.onClick
          });
        }
      });
    }

    // PrimaryActionButton - use the 'mod+A' hotkey if it is enabled
    if (typeName === 'PrimaryActionButton' && action?.props?.hidden !== true) {
      if (primaryActionHotkeyAdded) return;

      const hotkey = action?.props?.hotkey ?? 'mod+A';
      calcActions.push({
        hotkey,
        name:
          action?.props?.tooltip ?? action?.props?.title ?? t`Primary Action`,
        onClick: action?.props?.onClick
      });
      primaryActionHotkeyAdded = true;
    }
  });
  return calcActions;
}
