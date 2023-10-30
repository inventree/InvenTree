import { t } from '@lingui/macro';
import { Button, CopyButton as MantineCopyButton } from '@mantine/core';
import { IconCopy } from '@tabler/icons-react';

export function CopyButton({ value }: { value: any }) {
  return (
    <MantineCopyButton value={value}>
      {({ copied, copy }) => (
        <Button
          color={copied ? 'teal' : 'gray'}
          onClick={copy}
          title={t`copy to clipboard`}
          variant="subtle"
          compact
        >
          <IconCopy size={10} />
        </Button>
      )}
    </MantineCopyButton>
  );
}
