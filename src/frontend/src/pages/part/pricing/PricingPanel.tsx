import { t } from '@lingui/macro';
import { Accordion, Alert, Space, Stack, Text } from '@mantine/core';
import { IconExclamationCircle } from '@tabler/icons-react';
import { ReactNode } from 'react';

import { StylishText } from '../../../components/items/StylishText';

export default function PricingPanel({
  content,
  label,
  title,
  visible
}: {
  content: ReactNode;
  label: string;
  title: string;
  visible: boolean;
}): ReactNode {
  return (
    visible && (
      <Accordion.Item value={label}>
        <Accordion.Control>
          <StylishText size="lg">{title}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>{content}</Accordion.Panel>
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
