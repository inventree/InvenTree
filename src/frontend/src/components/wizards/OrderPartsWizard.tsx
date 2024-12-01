import { t } from '@lingui/macro';
import { Alert, Group, Table, Text } from '@mantine/core';
import { useCallback, useEffect, useState } from 'react';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { shortenString } from '../../functions/tables';
import useWizard from '../../hooks/UseWizard';
import { apiUrl } from '../../states/ApiState';
import { PartColumn } from '../../tables/ColumnRenderers';
import RemoveRowButton from '../buttons/RemoveRowButton';
import { StandaloneField } from '../forms/StandaloneField';

enum OrderPartsWizardSteps {
  SelectSuppliers = 0,
  SelectOrders = 1
}

/**
 * Attributes for each selected part
 * - part: The part instance
 * - supplier_part: The selected supplier part instance
 * - quantity: The quantity of the part to order
 * - errors: Error messages for each attribute
 */
interface PartOrderRecord {
  part: any;
  supplier_part: any;
  quantity: number;
  errors: any;
}

function SelectPartsStep({
  records,
  onRemovePart,
  onSelectSupplierPart,
  onSelectQuantity
}: {
  records: PartOrderRecord[];
  onRemovePart: (part: any) => void;
  onSelectSupplierPart: (partId: number, supplierPart: any) => void;
  onSelectQuantity: (partId: number, quantity: number) => void;
}) {
  if (records.length === 0) {
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
          <Table.Th>{t`Supplier Part`}</Table.Th>
          <Table.Th>{t`Quantity`}</Table.Th>
          <Table.Th />
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {records.map((record: PartOrderRecord) => (
          <Table.Tr key={record.part?.pk}>
            <Table.Td>
              <PartColumn part={record.part} />
            </Table.Td>
            <Table.Td>{record.part?.IPN}</Table.Td>
            <Table.Td>
              {shortenString({ str: record.part?.description, len: 50 })}
            </Table.Td>
            <Table.Td>
              <StandaloneField
                fieldName='supplier_part'
                hideLabels={true}
                error={record.errors?.supplier_part}
                fieldDefinition={{
                  field_type: 'related field',
                  api_url: apiUrl(ApiEndpoints.supplier_part_list),
                  model: ModelType.supplierpart,
                  required: true,
                  value: record.supplier_part?.pk,
                  onValueChange: (value, instance) => {
                    onSelectSupplierPart(record.part.pk, instance);
                  },
                  filters: {
                    part: record.part.pk,
                    active: true,
                    supplier_detail: true
                  }
                }}
              />
            </Table.Td>
            <Table.Td>
              <StandaloneField
                fieldName='quantity'
                hideLabels={true}
                error={record.errors?.quantity}
                fieldDefinition={{
                  field_type: 'number',
                  required: true,
                  value: record.quantity,
                  onValueChange: (value) => {
                    // TODO: This is very inefficient due to re-rendering
                    // onSelectQuantity(record.part.pk, value);
                  }
                }}
              />
            </Table.Td>
            <Table.Td>
              <Group gap='xs' wrap='nowrap'>
                <RemoveRowButton onClick={() => onRemovePart(record.part)} />
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
  // Track a list of selected parts
  const [selectedParts, setSelectedParts] = useState<PartOrderRecord[]>([]);

  // Remove a part from the selected parts list
  const removePart = useCallback(
    (part: any) => {
      setSelectedParts(
        selectedParts.filter(
          (record: PartOrderRecord) => record.part?.pk !== part.pk
        )
      );
    },
    [selectedParts]
  );

  // Select a supplier part for a part
  const selectSupplierPart = useCallback(
    (partId: number, supplierPart: any) => {
      const records = [...selectedParts];

      records.forEach((record: PartOrderRecord, index: number) => {
        if (record.part.pk === partId) {
          records[index].supplier_part = supplierPart;
        }
      });

      setSelectedParts(records);
    },
    [selectedParts]
  );

  // Select quantity for a part
  const selectQuantity = useCallback(
    (partId: number, quantity: number) => {
      const records = [...selectedParts];

      records.forEach((record: PartOrderRecord, index: number) => {
        if (record.part.pk === partId) {
          records[index].quantity = quantity;
        }
      });

      setSelectedParts(records);
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
            <SelectPartsStep
              records={selectedParts}
              onRemovePart={removePart}
              onSelectSupplierPart={selectSupplierPart}
              onSelectQuantity={selectQuantity}
            />
          );
        case OrderPartsWizardSteps.SelectOrders:
          return <Text>Well hello there</Text>;
      }
    },
    [selectedParts]
  );

  const canStepForward = useCallback(
    (step: number): boolean => {
      if (!selectedParts?.length) {
        wizard.setError(t`No parts selected`);
        wizard.setErrorDetail(t`You must select at least one part to order`);
        return false;
      }

      let result = true;
      const records = [...selectedParts];

      // Check for errors in each part
      selectedParts.forEach((record: PartOrderRecord, index: number) => {
        records[index].errors = {
          supplier_part: !record.supplier_part
            ? t`Supplier part is required`
            : null,
          quantity:
            !record.quantity || record.quantity <= 0
              ? t`Quantity is required`
              : null
        };

        // If any errors are found, set the result to false
        if (Object.values(records[index].errors).some((error) => error)) {
          result = false;
        }
      });

      setSelectedParts(records);

      if (!result) {
        wizard.setError(t`Invalid part selection`);
        wizard.setErrorDetail(
          t`Please correct the errors in the selected parts`
        );
      }

      return result;
    },
    [selectedParts]
  );

  // Create the wizard manager
  const wizard = useWizard({
    title: t`Order Parts`,
    steps: [t`Select Suppliers`, t`Select Purchase Orders`],
    renderStep: renderStep,
    canStepForward: canStepForward
  });

  // Reset the wizard to a known state when opened
  useEffect(() => {
    setSelectedParts(
      parts
        .filter((part) => part.purchaseable && part.active)
        .map((part) => {
          return {
            part: part,
            supplier_part: undefined,
            quantity: 1,
            errors: {}
          };
        })
    );
  }, [parts, wizard.opened]);

  return wizard;
}
