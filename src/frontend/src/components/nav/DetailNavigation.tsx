import { ActionIcon, Group, Text, Tooltip } from '@mantine/core';
import { IconChevronLeft, IconChevronRight } from '@tabler/icons-react';

import { t } from '@lingui/core/macro';
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
          onClick={
            navigation.previous?.onClick ?? ((event) => event.preventDefault())
          }
          data-disabled={!navigation.previous || undefined}
          aria-disabled={!navigation.previous}
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
          onClick={navigation.next?.onClick ?? ((event) => event.preventDefault())}
          data-disabled={!navigation.next || undefined}
          aria-disabled={!navigation.next}
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
