import { t } from '@lingui/macro';
import { NumberInput, Table } from '@mantine/core';
import { useCallback, useEffect, useState } from 'react';
import useWizard from '../../hooks/UseWizard';
import { PartColumn } from '../../tables/ColumnRenderers';

function SelectPartsStep({
  parts,
  onRemovePart
}: {
  parts: any[];
  onRemovePart: (part: any) => void;
}) {
  return (
    <Table striped withColumnBorders withTableBorder>
      <Table.Thead>
        <Table.Tr>
          <Table.Th>{t`Part`}</Table.Th>
          <Table.Th>{t`IPN`}</Table.Th>
          <Table.Th>{t`Description`}</Table.Th>
          <Table.Th>{t`Quantity`}</Table.Th>
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {parts.map((part) => (
          <Table.Tr key={part.pk}>
            <Table.Td>
              <PartColumn part={part} />
            </Table.Td>
            <Table.Td>{part.IPN}</Table.Td>
            <Table.Td>{part.description}</Table.Td>
            <Table.Td>
              <NumberInput
                min={0}
                max={100}
                defaultValue={0}
                placeholder={t`Quantity`}
              />
            </Table.Td>
          </Table.Tr>
        ))}
      </Table.Tbody>
    </Table>
  );
}

export default function OrderPartsWizard({
  parts
}: {
  parts: any[];
}) {
  const [selectedParts, setSelectedParts] = useState<any[]>([]);

  // Reset the selected parts when the parts list changes
  useEffect(() => {
    setSelectedParts(parts.filter((part) => part.purchaseable));
  }, [parts]);

  // Remove a part from the selected parts list
  const removePart = useCallback(
    (part: any) => {
      setSelectedParts(selectedParts.filter((p) => p.pk !== part.pk));
    },
    [selectedParts]
  );

  const renderStep = useCallback(
    (step: number) => {
      return (
        <SelectPartsStep parts={selectedParts} onRemovePart={removePart} />
      );
    },
    [selectedParts]
  );

  // Create the wizard manager
  const wizard = useWizard({
    title: t`Order Parts`,
    steps: [t`Select Parts`, t`Select Suppliers`, t`Select Orders`],
    renderStep: renderStep
  });

  return wizard;
}
