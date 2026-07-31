import { t } from '@lingui/core/macro';
import { ActionIcon, Group, Tooltip } from '@mantine/core';
import { IconChevronLeft, IconChevronRight } from '@tabler/icons-react';

interface NextPrevActionProps {
  prevPk?: number;
  nextPk?: number;
  onPrev: () => void;
  onNext: () => void;
}

export function NextPrevAction({
  prevPk,
  nextPk,
  onPrev,
  onNext
}: Readonly<NextPrevActionProps>) {
  return (
    <Group gap={5}>
      <Tooltip label={t`Previous`}>
        <ActionIcon
          data-testid='inventree-prev-item'
          disabled={prevPk === undefined}
          onClick={onPrev}
          variant='transparent'
        >
          <IconChevronLeft />
        </ActionIcon>
      </Tooltip>
      <Tooltip label={t`Next`}>
        <ActionIcon
          data-testid='inventree-next-item'
          disabled={nextPk === undefined}
          onClick={onNext}
          variant='transparent'
        >
          <IconChevronRight />
        </ActionIcon>
      </Tooltip>
    </Group>
  );
}
