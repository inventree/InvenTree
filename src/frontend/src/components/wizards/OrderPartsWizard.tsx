import { t } from '@lingui/macro';
import { Alert, Group, NumberInput, Table } from '@mantine/core';
import { useCallback, useEffect, useState } from 'react';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import useWizard from '../../hooks/UseWizard';
import { apiUrl } from '../../states/ApiState';
import { PartColumn } from '../../tables/ColumnRenderers';
import RemoveRowButton from '../buttons/RemoveRowButton';
import { StandaloneField } from '../forms/StandaloneField';

enum OrderPartsWizardSteps {
  SelectSuppliers = 0,
  SelectOrders = 1
}

function SelectPartsStep({
  parts,
  onRemovePart
}: {
  parts: any[];
  onRemovePart: (part: any) => void;
}) {
  if (parts.length === 0) {
    return (
      <Alert color='red' title={t`No parts selected`}>
        {t`No purchaseable parts selected`}
      </Alert>
    );
  }

  return (
    <Table striped withColumnBorders withTableBorder>
      <Table.Thead>
        <Table.Tr>
          <Table.Th>{t`Part`}</Table.Th>
          <Table.Th>{t`IPN`}</Table.Th>
          <Table.Th>{t`Description`}</Table.Th>
          <Table.Th>{t`Supplier`}</Table.Th>
          <Table.Th>{t`Quantity`}</Table.Th>
          <Table.Th />
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
              <StandaloneField
                fieldName='supplier'
                hideLabels={true}
                fieldDefinition={{
                  field_type: 'related field',
                  api_url: apiUrl(ApiEndpoints.supplier_part_list),
                  model: ModelType.supplierpart,
                  onValueChange: (value, record) => {
                    // TODO
                  },
                  filters: {
                    part: part.pk,
                    active: true,
                    supplier_detail: true
                  }
                }}
              />
            </Table.Td>
            <Table.Td>
              <NumberInput
                min={0}
                max={100}
                defaultValue={0}
                placeholder={t`Quantity`}
              />
            </Table.Td>
            <Table.Td>
              <Group gap='xs' wrap='nowrap'>
                <RemoveRowButton onClick={() => onRemovePart(part)} />
              </Group>
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

  // Render the select wizard step
  const renderStep = useCallback(
    (step: number) => {
      switch (step) {
        default:
        case OrderPartsWizardSteps.SelectSuppliers:
          return (
            <SelectPartsStep parts={selectedParts} onRemovePart={removePart} />
          );
      }
    },
    [selectedParts]
  );

  // Create the wizard manager
  const wizard = useWizard({
    title: t`Order Parts`,
    steps: [t`Select Suppliers`, t`Select Purchase Orders`],
    renderStep: renderStep
  });

  return wizard;
}
