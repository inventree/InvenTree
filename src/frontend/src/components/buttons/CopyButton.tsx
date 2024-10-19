import { t } from '@lingui/macro';
import {
  ActionIcon,
  Button,
  CopyButton as MantineCopyButton,
  type MantineSize,
  Text,
  Tooltip
} from '@mantine/core';

import { InvenTreeIcon } from '../../functions/icons';

export function CopyButton({
  value,
  label,
  content,
  size
}: Readonly<{
  value: any;
  label?: string;
  content?: JSX.Element;
  size?: MantineSize;
}>) {
  const ButtonComponent = label ? Button : ActionIcon;

  return (
    <MantineCopyButton value={value}>
      {({ copied, copy }) => (
        <Tooltip label={copied ? t`Copied` : t`Copy`} withArrow>
          <ButtonComponent
            color={copied ? 'teal' : 'gray'}
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
