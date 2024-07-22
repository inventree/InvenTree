import { t } from '@lingui/macro';
import {
  ActionIcon,
  Button,
  CopyButton as MantineCopyButton,
  Text,
  Tooltip
} from '@mantine/core';

import { InvenTreeIcon } from '../../functions/icons';

export function CopyButton({
  value,
  label
}: {
  value: any;
  label?: JSX.Element;
}) {
  const ButtonComponent = label ? Button : ActionIcon;

  return (
    <MantineCopyButton value={value}>
      {({ copied, copy }) => (
        <Tooltip label={copied ? t`Copied` : t`Copy`} withArrow>
          <ButtonComponent
            color={copied ? 'teal' : 'gray'}
            onClick={copy}
            variant="transparent"
            size="sm"
          >
            {copied ? (
              <InvenTreeIcon icon="check" />
            ) : (
              <InvenTreeIcon icon="copy" />
            )}

            {label && <Text ml={10}>{label}</Text>}
          </ButtonComponent>
        </Tooltip>
      )}
    </MantineCopyButton>
  );
}
