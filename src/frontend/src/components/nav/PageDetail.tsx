import { Group, Paper, Space, Stack, Text } from '@mantine/core';

import { StylishText } from '@lib/components/StylishText';
import { useInvenTreeHotkeys } from '@lib/functions/Events';
import { shortenString } from '@lib/functions/String';
import { t } from '@lingui/core/macro';
import { Fragment, type ReactNode, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { usePluginUIFeature } from '../../hooks/UsePluginUIFeature';
import { useUserSettingsState } from '../../states/SettingsStates';
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
  // duplicate
  useActionHotkeys(actions);

  // delete
  // create

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
          console.log(
            'useActionHotkeys dropdown action with hotkey',
            dropdownAction
          );
          calcActions.push({
            hotkey: dropdownAction.hotkey,
            name: dropdownAction.name,
            onClick: dropdownAction.onClick
          });
        }
      });
    }

    // PrimaryActionButton - use the 'mod+A' hotkey if it is enabled
    if (
      !primaryActionHotkeyAdded &&
      typeName === 'PrimaryActionButton' &&
      action?.props?.hidden !== true
    ) {
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
