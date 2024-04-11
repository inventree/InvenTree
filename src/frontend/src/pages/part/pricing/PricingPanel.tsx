import { Accordion, Paper } from '@mantine/core';
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
        <Accordion.Panel>
          <Paper p="sm">{content}</Paper>
        </Accordion.Panel>
      </Accordion.Item>
    )
  );
}
