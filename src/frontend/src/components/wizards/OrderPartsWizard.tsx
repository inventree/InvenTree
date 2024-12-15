import { t } from '@lingui/macro';
import { Alert, Group, Paper, Tooltip } from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import { IconShoppingCart } from '@tabler/icons-react';
import { DataTable } from 'mantine-datatable';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { useSupplierPartFields } from '../../forms/CompanyForms';
import { usePurchaseOrderFields } from '../../forms/PurchaseOrderForms';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import useWizard from '../../hooks/UseWizard';
import { apiUrl } from '../../states/ApiState';
import { PartColumn } from '../../tables/ColumnRenderers';
import { ActionButton } from '../buttons/ActionButton';
import { AddItemButton } from '../buttons/AddItemButton';
import RemoveRowButton from '../buttons/RemoveRowButton';
import { StandaloneField } from '../forms/StandaloneField';
import type { ApiFormFieldSet } from '../forms/fields/ApiFormField';
import Expand from '../items/Expand';

/**
 * Attributes for each selected part
 * - part: The part instance
 * - supplier_part: The selected supplier part instance
 * - purchase_order: The selected purchase order instance
 * - quantity: The quantity of the part to order
 * - errors: Error messages for each attribute
 */
interface PartOrderRecord {
  part: any;
  supplier_part: any;
  purchase_order: any;
  quantity: number;
  errors: any;
}

function SelectPartsStep({
  records,
  onRemovePart,
  onSelectSupplierPart,
  onSelectPurchaseOrder
}: {
  records: PartOrderRecord[];
  onRemovePart: (part: any) => void;
  onSelectSupplierPart: (partId: number, supplierPart: any) => void;
  onSelectPurchaseOrder: (partId: number, purchaseOrder: any) => void;
}) {
  const [selectedRecord, setSelectedRecord] = useState<PartOrderRecord | null>(
    null
  );

  const purchaseOrderFields = usePurchaseOrderFields({
    supplierId: selectedRecord?.supplier_part?.supplier
  });

  const newPurchaseOrder = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.purchase_order_list),
    title: t`New Purchase Order`,
    fields: purchaseOrderFields,
    successMessage: t`Purchase order created`,
    onFormSuccess: (response: any) => {
      onSelectPurchaseOrder(selectedRecord?.part.pk, response);
    }
  });

  const supplierPartFields = useSupplierPartFields({
    partId: selectedRecord?.part.pk
  });

  const newSupplierPart = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.supplier_part_list),
    title: t`New Supplier Part`,
    fields: supplierPartFields,
    successMessage: t`Supplier part created`,
    onFormSuccess: (response: any) => {
      onSelectSupplierPart(selectedRecord?.part.pk, response);
    }
  });

  const addToOrderFields: ApiFormFieldSet = useMemo(() => {
    return {
      order: {
        value: selectedRecord?.purchase_order?.pk,
        disabled: true
      },
      part: {
        value: selectedRecord?.supplier_part?.pk,
        disabled: true
      },
      reference: {},
      quantity: {
        // TODO: Auto-fill with the desired quantity
      },
      merge_items: {}
    };
  }, [selectedRecord]);

  const addToOrder = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.purchase_order_line_list),
    title: t`Add to Purchase Order`,
    fields: addToOrderFields,
    focus: 'quantity',
    initialData: {
      order: selectedRecord?.purchase_order?.pk,
      part: selectedRecord?.supplier_part?.pk,
      quantity: selectedRecord?.quantity
    },
    onFormSuccess: (response: any) => {
      // Remove the row from the list
      onRemovePart(selectedRecord?.part);
    },
    successMessage: t`Part added to purchase order`
  });

  const columns: any[] = useMemo(() => {
    return [
      {
        accessor: 'left_actions',
        title: ' ',
        width: '1%',
        render: (record: PartOrderRecord) => (
          <Group gap='xs' wrap='nowrap' justify='left'>
            <RemoveRowButton onClick={() => onRemovePart(record.part)} />
          </Group>
        )
      },
      {
        accessor: 'part',
        title: t`Part`,
        render: (record: PartOrderRecord) => (
          <Tooltip label={record.part?.description}>
            <Paper p='xs'>
              <PartColumn part={record.part} />
            </Paper>
          </Tooltip>
        )
      },
      {
        accessor: 'supplier_part',
        title: t`Supplier Part`,
        width: '40%',
        render: (record: PartOrderRecord) => (
          <Group gap='xs' wrap='nowrap' justify='left'>
            <Expand>
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
            </Expand>
            <AddItemButton
              tooltip={t`New supplier part`}
              tooltipAlignment='top'
              onClick={() => {
                setSelectedRecord(record);
                newSupplierPart.open();
              }}
            />
          </Group>
        )
      },
      {
        accessor: 'purchase_order',
        title: t`Purchase Order`,
        width: '40%',
        render: (record: PartOrderRecord) => (
          <Group gap='xs' wrap='nowrap' justify='left'>
            <Expand>
              <StandaloneField
                fieldName='purchase_order'
                hideLabels={true}
                fieldDefinition={{
                  field_type: 'related field',
                  api_url: apiUrl(ApiEndpoints.purchase_order_list),
                  model: ModelType.purchaseorder,
                  disabled: !record.supplier_part?.supplier,
                  value: record.purchase_order?.pk,
                  filters: {
                    supplier: record.supplier_part?.supplier,
                    outstanding: true
                  },
                  onValueChange: (value, instance) => {
                    onSelectPurchaseOrder(record.part.pk, instance);
                  }
                }}
              />
            </Expand>
            <AddItemButton
              tooltip={t`New purchase order`}
              tooltipAlignment='top'
              disabled={!record.supplier_part?.pk}
              onClick={() => {
                setSelectedRecord(record);
                newPurchaseOrder.open();
              }}
            />
          </Group>
        )
      },
      {
        accessor: 'right_actions',
        title: ' ',
        width: '1%',
        render: (record: PartOrderRecord) => (
          <Group grow gap='xs' wrap='nowrap' justify='right'>
            <ActionButton
              onClick={() => {
                setSelectedRecord(record);
                addToOrder.open();
              }}
              disabled={
                !record.supplier_part?.pk ||
                !record.quantity ||
                !record.purchase_order?.pk
              }
              icon={<IconShoppingCart />}
              tooltip={t`Add to selected purchase order`}
              tooltipAlignment='top'
              color='blue'
            />
          </Group>
        )
      }
    ];
  }, [onRemovePart]);

  if (records.length === 0) {
    return (
      <Alert color='red' title={t`No parts selected`}>
        {t`No purchaseable parts selected`}
      </Alert>
    );
  }

  return (
    <>
      <DataTable idAccessor='part.pk' columns={columns} records={records} />
      {newPurchaseOrder.modal}
      {newSupplierPart.modal}
      {addToOrder.modal}
    </>
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
      const records = selectedParts.filter(
        (record: PartOrderRecord) => record.part?.pk !== part.pk
      );

      setSelectedParts(records);

      // If no parts remain, close the wizard
      if (records.length === 0) {
        wizard.closeWizard();
        showNotification({
          title: t`Parts Added`,
          message: t`All selected parts added to a purchase order`,
          color: 'green'
        });
      }
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

  // Select purchase order for a part
  const selectPurchaseOrder = useCallback(
    (partId: number, purchaseOrder: any) => {
      const records = [...selectedParts];

      records.forEach((record: PartOrderRecord, index: number) => {
        if (record.part.pk === partId) {
          records[index].purchase_order = purchaseOrder;
        }
      });

      setSelectedParts(records);
    },
    [selectedParts]
  );

  // Render the select wizard step
  const renderStep = useCallback(
    (step: number) => {
      return (
        <SelectPartsStep
          records={selectedParts}
          onRemovePart={removePart}
          onSelectSupplierPart={selectSupplierPart}
          onSelectPurchaseOrder={selectPurchaseOrder}
        />
      );
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
    steps: [],
    renderStep: renderStep,
    canStepForward: canStepForward
  });

  // Reset the wizard to a known state when opened
  useEffect(() => {
    const records: PartOrderRecord[] = [];

    if (wizard.opened) {
      parts
        .filter((part) => part.purchaseable && part.active)
        .forEach((part) => {
          // Prevent duplicate entries based on pk
          if (
            !records.find(
              (record: PartOrderRecord) => record.part?.pk === part.pk
            )
          ) {
            records.push({
              part: part,
              supplier_part: undefined,
              purchase_order: undefined,
              quantity: 1,
              errors: {}
            });
          }
        });

      setSelectedParts(records);
    } else {
      setSelectedParts([]);
    }
  }, [wizard.opened]);

  return wizard;
}
