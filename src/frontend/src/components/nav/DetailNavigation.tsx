import { ActionIcon, Group, Text, Tooltip } from '@mantine/core';
import {
  IconCancel,
  IconChevronLeft,
  IconChevronRight
} from '@tabler/icons-react';

import { t } from '@lingui/core/macro';
import { useNavigate } from 'react-router-dom';
import { removeDetailNavigationParams } from '../../functions/DetailNavigation';
import type { DetailNavigationState } from '../../hooks/UseDetailNavigation';

export function DetailNavigation({
  navigation
}: Readonly<{ navigation: DetailNavigationState }>) {
  const hasNavigation = Boolean(
    navigation.previous ||
      navigation.next ||
      navigation.position ||
      navigation.isLoading
  );
  const navigate = useNavigate();

  function handleClear() {
    const url = new URL(window.location.href);
    removeDetailNavigationParams(url.searchParams);
    navigate(url);
  }

  if (!hasNavigation) {
    return null;
  }

  return (
    <Group
      gap={5}
      justify='right'
      wrap='nowrap'
      align='center'
      data-testid='detail-navigation'
      style={{ flexShrink: 0, minHeight: 36 }}
    >
      <Tooltip
        label={t`Remove navigation filters from current view`}
        position='top'
      >
        <ActionIcon onClick={handleClear} size='md' variant='subtle'>
          <IconCancel size='1.25rem' />
        </ActionIcon>
      </Tooltip>
      {navigation.position && (
        <Text
          size='xs'
          c='dimmed'
          px={4}
          aria-label='detail-navigation-position'
        >
          {t`${navigation.position.current} of ${navigation.position.total}`}
        </Text>
      )}
      <Tooltip label={t`Previous`} position='top'>
        <ActionIcon
          component='a'
          href={navigation.previous?.href}
          onClick={navigation.previous?.onClick}
          disabled={!navigation.previous}
          size='md'
          variant='subtle'
          aria-label={t`Previous`}
        >
          <IconChevronLeft size='1.25rem' />
        </ActionIcon>
      </Tooltip>
      <Tooltip label={t`Next`} position='top'>
        <ActionIcon
          component='a'
          href={navigation.next?.href}
          onClick={navigation.next?.onClick}
          disabled={!navigation.next}
          size='md'
          variant='subtle'
          aria-label={t`Next`}
        >
          <IconChevronRight size='1.25rem' />
        </ActionIcon>
      </Tooltip>
    </Group>
  );
}
