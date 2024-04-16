import { t } from '@lingui/macro';
import {
  Accordion,
  AccordionControlProps,
  Alert,
  Box,
  Space,
  Stack,
  Text,
  Tooltip
} from '@mantine/core';
import { IconAlertCircle, IconExclamationCircle } from '@tabler/icons-react';
import { ReactNode } from 'react';

import { StylishText } from '../../../components/items/StylishText';

function AccordionControl(props: AccordionControlProps) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center' }}>
      {props.disabled && (
        <Tooltip
          label={t`No data available`}
          children={<IconAlertCircle size="1rem" color="gray" />}
        />
      )}
      <Accordion.Control
        {...props}
        pl={props.disabled ? '0.25rem' : '1.25rem'}
      />
    </Box>
  );
}

export default function PricingPanel({
  content,
  label,
  title,
  visible,
  disabled = undefined
}: {
  content: ReactNode;
  label: string;
  title: string;
  visible: boolean;
  disabled?: boolean | undefined;
}): ReactNode {
  const is_disabled = disabled === undefined ? false : disabled;
  return (
    visible && (
      <Accordion.Item value={label}>
        <AccordionControl disabled={is_disabled}>
          <StylishText size="lg">{title}</StylishText>
        </AccordionControl>
        <Accordion.Panel>{!is_disabled && content}</Accordion.Panel>
      </Accordion.Item>
    )
  );
}

export function NoPricingData() {
  return (
    <Stack spacing="xs">
      <Alert icon={<IconExclamationCircle />} color="blue" title={t`No Data`}>
        <Text>{t`No pricing data available`}</Text>
      </Alert>
      <Space />
    </Stack>
  );
}
