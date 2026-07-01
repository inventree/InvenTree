import { t } from '@lingui/core/macro';
import {
  ActionIcon,
  Anchor,
  Group,
  HoverCard,
  Stack,
  Text
} from '@mantine/core';
import type { ReactNode } from 'react';
import type { NavigateFunction } from 'react-router-dom';

import { ModelInformationDict } from '@lib/enums/ModelInformation';
import type { ModelType } from '@lib/enums/ModelType';
import { getDetailUrl, navigateToLink } from '@lib/index';
import { IconLink } from '@tabler/icons-react';

/**
 * Wraps children in a HoverCard showing the model label, pk, and a "View
 * details" link for the given instance. Renders children directly (no card)
 * when model or pk is absent.
 */
export function ModelHoverCard({
  children,
  model,
  pk,
  navigate
}: {
  children: ReactNode;
  model: ModelType | undefined;
  pk: number | null | undefined;
  navigate?: NavigateFunction | null;
}) {
  const modelInfo = model ? ModelInformationDict[model] : undefined;

  if (!modelInfo || !pk) {
    return <>{children}</>;
  }

  const detailUrl = getDetailUrl(model!, pk, true);

  return (
    <HoverCard
      position='top-end'
      withinPortal
      openDelay={500}
      closeDelay={100}
      zIndex={99999}
    >
      <HoverCard.Target>
        <span>{children}</span>
      </HoverCard.Target>
      <HoverCard.Dropdown>
        <Stack gap='xs'>
          <Group justify='space-between'>
            <Text size='sm' fw='bold'>
              {modelInfo.label()}
            </Text>
            <Text size='xs'>{`[${t`ID`}: ${pk}]`}</Text>
          </Group>
          {detailUrl && (
            <Anchor
              href={detailUrl}
              target='_blank'
              onClick={(event) => {
                if (navigate) navigateToLink(detailUrl, navigate, event);
              }}
            >
              <Group gap='xs' wrap='nowrap'>
                <ActionIcon variant='transparent' size='xs'>
                  <IconLink />
                </ActionIcon>
                <Text size='sm'>{t`View details`}</Text>
              </Group>
            </Anchor>
          )}
        </Stack>
      </HoverCard.Dropdown>
    </HoverCard>
  );
}
