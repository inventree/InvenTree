import { t } from '@lingui/core/macro';
import {
  ActionIcon,
  Button,
  type DefaultMantineColor,
  CopyButton as MantineCopyButton,
  type MantineSize,
  Text,
  Tooltip
} from '@mantine/core';

import { InvenTreeIcon } from '../../functions/icons';

import type { JSX } from 'react';

export function CopyButton({
  value,
  label,
  content,
  size,
  color = 'gray'
}: Readonly<{
  value: any;
  label?: string;
  content?: JSX.Element;
  size?: MantineSize;
  color?: DefaultMantineColor;
}>) {
  const ButtonComponent = label ? Button : ActionIcon;

  return (
    <MantineCopyButton value={value}>
      {({ copied, copy }) => (
        <Tooltip label={copied ? t`Copied` : t`Copy`} withArrow>
          <ButtonComponent
            color={copied ? 'teal' : color}
            onClick={copy}
            variant='transparent'
            size={size ?? 'sm'}
          >
            {copied ? (
              <InvenTreeIcon icon='check' />
            ) : (
              <InvenTreeIcon icon='copy' />
            )}
            {content}
            {label && (
              <Text p={size ?? 'sm'} size={size ?? 'sm'}>
                {label}
              </Text>
            )}
          </ButtonComponent>
        </Tooltip>
      )}
    </MantineCopyButton>
  );
}
