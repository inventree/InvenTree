import { ActionButton } from '@lib/components/ActionButton';
import { AddItemButton } from '@lib/components/AddItemButton';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import { formatDecimal } from '@lib/functions/Formatting';
import type { ApiFormFieldSet } from '@lib/types/Forms';
import { t } from '@lingui/core/macro';
import {
  ActionIcon,
  Alert,
  Divider,
  Group,
  HoverCard,
  Loader,
  Paper,
  Stack,
  Text,
  Tooltip
} from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import {
  IconExclamationCircle,
  IconInfoCircle,
  IconShoppingCart
} from '@tabler/icons-react';
import { DataTable } from 'mantine-datatable';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useSupplierPartFields } from '../../forms/CompanyForms';
import { usePurchaseOrderFields } from '../../forms/PurchaseOrderForms';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import useWizard from '../../hooks/UseWizard';
import { RenderPartColumn } from '../../tables/ColumnRenderers';
import { CopyButton } from '../buttons/CopyButton';
import RemoveRowButton from '../buttons/RemoveRowButton';
import { StandaloneField } from '../forms/StandaloneField';
import Expand from '../items/Expand';

/**
 * Render the "requirements" info for a part
 * This fetches the information dynamically from the API
 */
function PartRequirementsInfo({
  partId,
  onQuantityChange
}: {
  partId: number | string;
  onQuantityChange?: (quantity: number) => void;
}) {
  const [requiredQuantity, setRequiredQuantity] = useState<number>(0);

  // Notify parent component of quantity change
  useEffect(() => {
    onQuantityChange?.(requiredQuantity);
  }, [requiredQuantity]);

  const requirements = useInstance({
    endpoint: ApiEndpoints.part_requirements,
    pk: partId,
    hasPrimaryKey: true,
    defaultValue: {}
  });

  const widget = useMemo(() => {
    if (
      requirements.instanceQuery.isFetching ||
      requirements.instanceQuery.isLoading
    ) {
      return <Loader size='sm' />;
    }

    if (requirements.instanceQuery.isError) {
      return (
        <Tooltip label={t`Error fetching part requirements`}>
          <ActionIcon variant='transparent' color='red'>
            <IconExclamationCircle />
          </ActionIcon>
        </Tooltip>
      );
    }

    // Calculate the total requirements
    const buildRequirements =
      requirements.instance?.required_for_build_orders || 0;
    const salesRequirements =
      requirements.instance?.required_for_sales_orders || 0;
    const totalRequirements = buildRequirements + salesRequirements;

    const building = requirements.instance?.building || 0;
    const ordering = requirements.instance?.ordering || 0;
    const incoming = building + ordering;

    const inStock = requirements.instance?.total_stock || 0;

    const required = Math.max(0, totalRequirements - inStock - incoming);

    setRequiredQuantity(required);

    return (
      <HoverCard position='bottom-end'>
        <HoverCard.Target>
          <ActionIcon
            variant='transparent'
            color={required > 0 ? 'blue' : 'green'}
            size='sm'
          >
            <IconInfoCircle />
          </ActionIcon>
        </HoverCard.Target>
        <HoverCard.Dropdown>
          <Stack gap='xs'>
            <Text>{t`Requirements`}</Text>
            <Divider />
            {buildRequirements > 0 && (
              <Group justify='space-between'>
                <Text size='xs'>{t`Build Requirements`}</Text>
                <Text size='xs'>{formatDecimal(buildRequirements)}</Text>
              </Group>
            )}
            {salesRequirements > 0 && (
              <Group justify='space-between'>
                <Text size='xs'>{t`Sales Requirements`}</Text>
                <Text size='xs'>{formatDecimal(salesRequirements)}</Text>
              </Group>
            )}
            {inStock > 0 && (
              <Group justify='space-between'>
                <Text size='xs'>{t`In Stock`}</Text>
                <Text size='xs'>{formatDecimal(inStock)}</Text>
              </Group>
            )}
            {ordering > 0 && (
              <Group justify='space-between'>
                <Text size='xs'>{t`On Order`}</Text>
                <Text size='xs'>{formatDecimal(ordering)}</Text>
              </Group>
            )}
            {building > 0 && (
              <Group justify='space-between'>
                <Text size='xs'>{t`In Production`}</Text>
                <Text size='xs'>{formatDecimal(building)}</Text>
              </Group>
            )}
            <Group justify='space-between'>
              <Text size='xs'>{t`Required Quantity`}</Text>
              <Text size='xs'>{formatDecimal(required)}</Text>
            </Group>
          </Stack>
        </HoverCard.Dropdown>
      </HoverCard>
    );
  }, [
    requirements.instanceQuery.isFetching,
    requirements.instanceQuery.isLoading,
    requirements.instanceQuery.isError,
    requirements.instance,
    setRequiredQuantity
  ]);

  return widget;
}

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
  onSelectQuantity,
  onSelectSupplierPart,
  onSelectPurchaseOrder
}: {
  records: PartOrderRecord[];
  onRemovePart: (part: any) => void;
  onSelectQuantity: (partId: number, quantity: number) => void;
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
      purchase_price: {},
      purchase_price_currency: {},
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
            <RemoveRowButton
              tooltipAlignment={'top-start'}
              onClick={() => onRemovePart(record.part)}
            />
          </Group>
        )
      },
      {
        accessor: 'part',
        title: t`Part`,
        render: (record: PartOrderRecord) => (
          <Tooltip label={record.part?.description}>
            <Paper p='xs'>
              <RenderPartColumn part={record.part} />
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
                  placeholder: t`Select supplier part`,
                  required: true,
                  autoFill: true,
                  value: record.supplier_part?.pk,
                  onValueChange: (value, instance) => {
                    onSelectSupplierPart(record.part.pk, instance);
                  },
                  filters: {
                    part: record.part.pk,
                    active: true,
                    part_detail: true,
                    supplier_detail: true
                  }
                }}
              />
            </Expand>
            <CopyButton
              disabled={!record.supplier_part?.pk}
              value={record.supplier_part?.SKU}
              tooltipPosition='top-end'
              tooltip={t`Copy supplier part number`}
            />
            <AddItemButton
              tooltip={t`New supplier part`}
              tooltipAlignment='top-end'
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
                  placeholder: t`Select purchase order`,
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
              tooltipAlignment='top-end'
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
        accessor: 'quantity',
        title: t`Quantity`,
        width: 150,
        render: (record: PartOrderRecord) => (
          <Group gap='xs' wrap='nowrap'>
            <StandaloneField
              fieldName='quantity'
              hideLabels={true}
              error={record.errors?.quantity}
              fieldDefinition={{
                field_type: 'number',
                required: true,
                value: record.quantity,
                onValueChange: (value) => {
                  onSelectQuantity(record.part.pk, value);
                }
              }}
            />
            <PartRequirementsInfo
              partId={record.part.pk}
              onQuantityChange={(quantity: number) =>
                onSelectQuantity(record.part.pk, quantity)
              }
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
              tooltipAlignment='top-end'
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

  // Select a quantity to order
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
          onSelectQuantity={selectQuantity}
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
            // TODO: Make this calculation generic and reusable
            // Calculate the "to order" quantity
            const required =
              (part.minimum_stock ?? 0) +
              (part.required_for_build_orders ?? 0) +
              (part.required_for_sales_orders ?? 0);
            const on_hand = part.total_in_stock ?? 0;
            const on_order = part.ordering ?? 0;
            const in_production = part.building ?? 0;

            const to_order = required - on_hand - on_order - in_production;

            records.push({
              part: part,
              supplier_part: undefined,
              purchase_order: undefined,
              quantity: Math.max(to_order, 0),
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
