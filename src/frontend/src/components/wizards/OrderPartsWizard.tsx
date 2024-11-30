import { t } from '@lingui/macro';
import { Stack, Text } from '@mantine/core';
import { useCallback, useEffect, useState } from 'react';
import useWizard from '../../hooks/UseWizard';

export default function OrderPartsWizard({
  parts
}: {
  parts: any[];
}) {
  const [selectedParts, setSelectedParts] = useState<any[]>([]);

  useEffect(() => {
    setSelectedParts(parts);
  }, [parts]);

  const renderStep = useCallback(
    (step: number) => {
      return (
        <Stack gap='xs'>
          <Text>Step: {step}</Text>
          <Text>Parts: {selectedParts.length}</Text>
        </Stack>
      );
    },
    [selectedParts]
  );

  return useWizard({
    title: t`Order Parts`,
    steps: [t`Select Parts`, t`Select Suppliers`, t`Select Orders`],
    renderStep: renderStep
  });
}
