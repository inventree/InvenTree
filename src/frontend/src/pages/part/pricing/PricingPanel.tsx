import { t } from '@lingui/macro';
import {
  Accordion,
  type AccordionControlProps,
  Alert,
  Box,
  Center,
  Loader,
  Space,
  Stack,
  Text,
  Tooltip
} from '@mantine/core';
import { IconAlertCircle, IconExclamationCircle } from '@tabler/icons-react';
import type { ReactNode } from 'react';

import { StylishText } from '../../../components/items/StylishText';
import type { panelOptions } from '../PartPricingPanel';

function AccordionControl(props: AccordionControlProps) {
  return (
    <Box style={{ display: 'flex', alignItems: 'center' }}>
      {props.disabled && (
        <Tooltip label={t`No data available`}>
          <IconAlertCircle size='1rem' color='gray' />
        </Tooltip>
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
  label: panelOptions;
  title: string;
  visible: boolean;
  disabled?: boolean;
}): ReactNode {
  const is_disabled = disabled ?? false;
  return (
    visible && (
      <Accordion.Item value={label} id={label}>
        <AccordionControl disabled={is_disabled}>
          <StylishText size='lg'>{title}</StylishText>
        </AccordionControl>
        <Accordion.Panel>{!is_disabled && content}</Accordion.Panel>
      </Accordion.Item>
    )
  );
}

export function NoPricingData() {
  return (
    <Stack gap='xs'>
      <Alert icon={<IconExclamationCircle />} color='blue' title={t`No Data`}>
        <Text>{t`No pricing data available`}</Text>
      </Alert>
      <Space />
    </Stack>
  );
}

export function LoadingPricingData() {
  return (
    <Center>
      <Stack gap='xs'>
        <Text>{t`Loading pricing data`}</Text>
        <Loader />
      </Stack>
    </Center>
  );
}
