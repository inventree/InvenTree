import { t } from '@lingui/core/macro';
import { Alert, Divider, List, Stack, Table } from '@mantine/core';
import {
  IconCalendar,
  IconInfoCircle,
  IconLink,
  IconList,
  IconSitemap,
  IconTruckDelivery,
  IconUser,
  IconUsersGroup
} from '@tabler/icons-react';
import { useEffect, useMemo, useState } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import RemoveRowButton from '../components/buttons/RemoveRowButton';
import { StandaloneField } from '../components/forms/StandaloneField';

import { ProgressBar } from '@lib/components/ProgressBar';
import { apiUrl } from '@lib/functions/Api';
import type { ApiFormFieldSet, ApiFormFieldType } from '@lib/types/Forms';
import {
  TableFieldErrorWrapper,
  type TableFieldRowProps
} from '../components/forms/fields/TableField';
import { StatusRenderer } from '../components/render/StatusRenderer';
import { RenderStockItem } from '../components/render/Stock';
import { useCreateApiFormModal } from '../hooks/UseForm';
import {
  useBatchCodeGenerator,
  useSerialNumberGenerator
} from '../hooks/UseGenerator';
import { useGlobalSettingsState } from '../states/SettingsStates';
import { PartColumn } from '../tables/ColumnRenderers';

/**
 * Field set for BuildOrder forms
 */
export function useBuildOrderFields({
  create,
  modalId
}: {
  create: boolean;
  modalId: string;
}): ApiFormFieldSet {
  const [destination, setDestination] = useState<number | null | undefined>(
    null
  );

  const [batchCode, setBatchCode] = useState<string>('');

  const batchGenerator = useBatchCodeGenerator({
    modalId: modalId,
    onGenerate: (value: any) => {
      setBatchCode((batch: any) => batch || value);
    }
  });

  const globalSettings = useGlobalSettingsState();

  return useMemo(() => {
    const fields: ApiFormFieldSet = {
      reference: {},
      part: {
        disabled: !create,
        filters: {
          assembly: true,
          virtual: false,
          active: globalSettings.isSet('BUILDORDER_REQUIRE_ACTIVE_PART')
            ? true
            : undefined,
          locked: globalSettings.isSet('BUILDORDER_REQUIRE_LOCKED_PART')
            ? true
            : undefined
        },
        onValueChange(value: any, record?: any) {
          // Adjust the destination location for the build order
          if (record) {
            setDestination(
              record.default_location || record.category_default_location
            );
          }

          batchGenerator.update({
            part: value
          });
        }
      },
      title: {},
      quantity: {},
      project_code: {
        icon: <IconList />
      },
      priority: {},
      parent: {
        icon: <IconSitemap />,
        filters: {
          part_detail: true
        }
      },
      sales_order: {
        icon: <IconTruckDelivery />
      },
      batch: {
        placeholder:
          batchGenerator.result &&
          `${t`Next batch code`}: ${batchGenerator.result}`,
        value: batchCode,
        onValueChange: (value: any) => setBatchCode(value)
      },
      start_date: {
        icon: <IconCalendar />
      },
      target_date: {
        icon: <IconCalendar />
      },
      take_from: {},
      destination: {
        filters: {
          structural: false
        },
        value: destination
      },
      link: {
        icon: <IconLink />
      },
      issued_by: {
        icon: <IconUser />,
        filters: {
          is_active: true
        }
      },
      responsible: {
        icon: <IconUsersGroup />,
        filters: {
          is_active: true
        }
      },
      external: {}
    };

    if (!globalSettings.isSet('PROJECT_CODES_ENABLED', true)) {
      delete fields.project_code;
    }

    if (!globalSettings.isSet('BUILDORDER_EXTERNAL_BUILDS', true)) {
      delete fields.external;
    }

    return fields;
  }, [create, destination, batchCode, batchGenerator.result, globalSettings]);
}

export function useBuildOrderOutputFields({
  build,
  modalId
}: {
  build: any;
  modalId: string;
}): ApiFormFieldSet {
  const trackable: boolean = useMemo(() => {
    return build.part_detail?.trackable ?? false;
  }, [build.part_detail]);

  const [location, setLocation] = useState<number | null>(null);

  useEffect(() => {
    setLocation(build.location || build.part_detail?.default_location || null);
  }, [build.location, build.part_detail]);

  const [quantity, setQuantity] = useState<number>(0);

  useEffect(() => {
    const build_quantity = build.quantity ?? 0;
    const build_complete = build.completed ?? 0;

    setQuantity(Math.max(0, build_quantity - build_complete));
  }, [build]);

  const serialGenerator = useSerialNumberGenerator({
    modalId: modalId,
    initialQuery: {
      part: build.part || build.part_detail?.pk
    }
  });

  const batchGenerator = useBatchCodeGenerator({
    modalId: modalId,
    initialQuery: {
      part: build.part || build.part_detail?.pk,
      quantity: build.quantity
    }
  });

  return useMemo(() => {
    return {
      quantity: {
        value: quantity,
        onValueChange: (value: any) => {
          setQuantity(value);
        }
      },
      serial_numbers: {
        hidden: !trackable,
        placeholder:
          serialGenerator.result &&
          `${t`Next serial number`}: ${serialGenerator.result}`
      },
      batch_code: {
        placeholder:
          batchGenerator.result &&
          `${t`Next batch code`}: ${batchGenerator.result}`
      },
      location: {
        value: location,
        onValueChange: (value: any) => {
          setQuantity(value);
        }
      },
      auto_allocate: {
        hidden: !trackable
      }
    };
  }, [quantity, batchGenerator.result, serialGenerator.result, trackable]);
}

function BuildOutputFormRow({
  props,
  record
}: Readonly<{
  props: TableFieldRowProps;
  record: any;
}>) {
  const serial = useMemo(() => {
    if (record.serial) {
      return `# ${record.serial}`;
    } else {
      return `${t`Quantity`}: ${record.quantity}`;
    }
  }, [record]);

  return (
    <>
      <Table.Tr>
        <Table.Td>
          <PartColumn part={record.part_detail} />
        </Table.Td>
        <Table.Td>
          <TableFieldErrorWrapper props={props} errorKey='output'>
            {serial}
          </TableFieldErrorWrapper>
        </Table.Td>
        <Table.Td>{record.batch}</Table.Td>
        <Table.Td>
          <StatusRenderer
            status={record.status}
            type={ModelType.stockitem}
          />{' '}
        </Table.Td>
        <Table.Td style={{ width: '1%', whiteSpace: 'nowrap' }}>
          <RemoveRowButton onClick={() => props.removeFn(props.idx)} />
        </Table.Td>
      </Table.Tr>
    </>
  );
}

export function useCompleteBuildOutputsForm({
  build,
  outputs,
  onFormSuccess
}: {
  build: any;
  outputs: any[];
  onFormSuccess: (response: any) => void;
}) {
  const [location, setLocation] = useState<number | null>(null);

  useEffect(() => {
    if (location) {
      return;
    }

    setLocation(
      build.destination || build.part_detail?.default_location || null
    );
  }, [location, build.destination, build.part_detail]);

  const buildOutputCompleteFields: ApiFormFieldSet = useMemo(() => {
    return {
      outputs: {
        field_type: 'table',
        value: outputs.map((output: any) => {
          return {
            output: output.pk
          };
        }),
        modelRenderer: (row: TableFieldRowProps) => {
          const record = outputs.find((output) => output.pk == row.item.output);
          return (
            <BuildOutputFormRow props={row} record={record} key={record.pk} />
          );
        },
        headers: [
          { title: t`Part` },
          { title: t`Build Output` },
          { title: t`Batch` },
          { title: t`Status` },
          { title: '', style: { width: '50px' } }
        ]
      },
      status_custom_key: {},
      location: {
        filters: {
          structural: false
        },
        value: location,
        onValueChange: (value: any) => {
          setLocation(value);
        }
      },
      notes: {},
      accept_incomplete_allocation: {}
    };
  }, [location, outputs]);

  return useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.build_output_complete, build.pk),
    method: 'POST',
    title: t`Complete Build Outputs`,
    fields: buildOutputCompleteFields,
    onFormSuccess: onFormSuccess,
    successMessage: t`Build outputs have been completed`,
    size: '80%'
  });
}

/*
 * Dynamic form for scraping multiple build outputs
 */
export function useScrapBuildOutputsForm({
  build,
  outputs,
  onFormSuccess
}: {
  build: any;
  outputs: any[];
  onFormSuccess: (response: any) => void;
}) {
  const [location, setLocation] = useState<number | null>(null);

  useEffect(() => {
    if (location) {
      return;
    }

    setLocation(
      build.destination || build.part_detail?.default_location || null
    );
  }, [location, build.destination, build.part_detail]);

  const buildOutputScrapFields: ApiFormFieldSet = useMemo(() => {
    return {
      outputs: {
        field_type: 'table',
        value: outputs.map((output: any) => {
          return {
            output: output.pk,
            quantity: output.quantity
          };
        }),
        modelRenderer: (row: TableFieldRowProps) => {
          const record = outputs.find((output) => output.pk == row.item.output);
          return (
            <BuildOutputFormRow props={row} record={record} key={record.pk} />
          );
        },
        headers: [
          { title: t`Part` },
          { title: t`Stock Item` },
          { title: t`Batch` },
          { title: t`Status` },
          { title: '', style: { width: '50px' } }
        ]
      },
      location: {
        value: location,
        onValueChange: (value) => {
          setLocation(value);
        }
      },
      notes: {},
      discard_allocations: {}
    };
  }, [location, outputs]);

  return useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.build_output_scrap, build.pk),
    method: 'POST',
    title: t`Scrap Build Outputs`,
    preFormContent: (
      <Alert title={t`Scrap Build Outputs`} color='yellow'>
        <List>
          <List.Item>
            {t`Selected build outputs will be completed, but marked as scrapped`}
          </List.Item>
          <List.Item>{t`Allocated stock items will be consumed`}</List.Item>
        </List>
      </Alert>
    ),
    fields: buildOutputScrapFields,
    onFormSuccess: onFormSuccess,
    successMessage: t`Build outputs have been scrapped`,
    size: '80%'
  });
}

export function useCancelBuildOutputsForm({
  build,
  outputs,
  onFormSuccess
}: {
  build: any;
  outputs: any[];
  onFormSuccess: (response: any) => void;
}) {
  const buildOutputCancelFields: ApiFormFieldSet = useMemo(() => {
    return {
      outputs: {
        field_type: 'table',
        value: outputs.map((output: any) => {
          return {
            output: output.pk
          };
        }),
        modelRenderer: (row: TableFieldRowProps) => {
          const record = outputs.find((output) => output.pk == row.item.output);
          return (
            <BuildOutputFormRow props={row} record={record} key={record.pk} />
          );
        },
        headers: [
          { title: t`Part` },
          { title: t`Stock Item` },
          { title: t`Batch` },
          { title: t`Status` },
          { title: '', style: { width: '50px' } }
        ]
      }
    };
  }, [outputs]);

  return useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.build_output_delete, build.pk),
    method: 'POST',
    title: t`Cancel Build Outputs`,
    preFormContent: (
      <Alert title={t`Cancel Build Outputs`} color='yellow'>
        <List>
          <List.Item>{t`Selected build outputs will be removed`}</List.Item>
          <List.Item>
            {t`Allocated stock items will be returned to stock`}
          </List.Item>
        </List>
      </Alert>
    ),
    fields: buildOutputCancelFields,
    onFormSuccess: onFormSuccess,
    successMessage: t`Build outputs have been cancelled`,
    size: '80%'
  });
}

// Construct a single row in the 'allocate stock to build' table
function BuildAllocateLineRow({
  props,
  output,
  record,
  sourceLocation
}: Readonly<{
  props: TableFieldRowProps;
  output: any;
  record: any;
  sourceLocation: number | undefined;
}>) {
  const stockField: ApiFormFieldType = useMemo(() => {
    return {
      field_type: 'related field',
      api_url: apiUrl(ApiEndpoints.stock_item_list),
      model: ModelType.stockitem,
      autoFill: !!output?.serial,
      autoFillFilters: {
        serial: output?.serial
      },
      filters: {
        available: true,
        part_detail: true,
        location_detail: true,
        bom_item: record.bom_item,
        location: sourceLocation,
        cascade: sourceLocation ? true : undefined
      },
      value: props.item.stock_item,
      name: 'stock_item',
      onValueChange: (value: any, instance: any) => {
        props.changeFn(props.idx, 'stock_item', value);

        // Update the allocated quantity based on the selected stock item
        if (instance) {
          const available = instance.quantity - instance.allocated;

          if (available < props.item.quantity) {
            props.changeFn(
              props.idx,
              'quantity',
              Math.min(props.item.quantity, available)
            );
          }
        }
      }
    };
  }, [record, props]);

  const quantityField: ApiFormFieldType = useMemo(() => {
    return {
      field_type: 'number',
      name: 'quantity',
      required: true,
      value: props.item.quantity,
      onValueChange: (value: any) => {
        props.changeFn(props.idx, 'quantity', value);
      }
    };
  }, [props]);

  return (
    <Table.Tr key={`table-row-${record.pk}`}>
      <Table.Td>
        <PartColumn part={record.part_detail} />
      </Table.Td>
      <Table.Td>
        <ProgressBar
          value={record.allocatedQuantity}
          maximum={record.requiredQuantity}
          progressLabel
        />
      </Table.Td>
      <Table.Td>
        <StandaloneField
          fieldName='stock_item'
          fieldDefinition={stockField}
          error={props.rowErrors?.stock_item?.message}
        />
      </Table.Td>
      <Table.Td>
        <StandaloneField
          fieldName='quantity'
          fieldDefinition={quantityField}
          error={props.rowErrors?.quantity?.message}
        />
      </Table.Td>
      <Table.Td>
        <RemoveRowButton onClick={() => props.removeFn(props.idx)} />
      </Table.Td>
    </Table.Tr>
  );
}

/*
 * Dynamic form for allocating stock against multiple build order line items
 */
export function useAllocateStockToBuildForm({
  buildId,
  output,
  outputId,
  build,
  lineItems,
  onFormSuccess
}: {
  buildId?: number;
  output?: any;
  outputId?: number | null;
  build?: any;
  lineItems: any[];
  onFormSuccess: (response: any) => void;
}) {
  const [sourceLocation, setSourceLocation] = useState<number | undefined>(
    undefined
  );

  const buildAllocateFields: ApiFormFieldSet = useMemo(() => {
    const fields: ApiFormFieldSet = {
      items: {
        field_type: 'table',
        value: [],
        headers: [
          { title: t`Part`, style: { minWidth: '175px' } },
          { title: t`Allocated`, style: { minWidth: '175px' } },
          { title: t`Stock Item`, style: { width: '100%' } },
          { title: t`Quantity`, style: { minWidth: '175px' } },
          { title: '', style: { width: '50px' } }
        ],
        modelRenderer: (row: TableFieldRowProps) => {
          // Find the matching record from the passed 'lineItems'
          const record =
            lineItems.find((item) => item.pk == row.item.build_line) ?? {};
          return (
            <BuildAllocateLineRow
              key={row.idx}
              output={output}
              props={row}
              record={record}
              sourceLocation={sourceLocation}
            />
          );
        }
      }
    };

    return fields;
  }, [output, lineItems, sourceLocation]);

  useEffect(() => {
    setSourceLocation(build?.take_from);
  }, [build?.take_from]);

  const sourceLocationField: ApiFormFieldType = useMemo(() => {
    return {
      field_type: 'related field',
      api_url: apiUrl(ApiEndpoints.stock_location_list),
      model: ModelType.stocklocation,
      required: false,
      label: t`Source Location`,
      description: t`Select the source location for the stock allocation`,
      name: 'source_location',
      value: build?.take_from,
      onValueChange: (value: any) => {
        setSourceLocation(value);
      }
    };
  }, [build?.take_from]);

  const preFormContent = useMemo(() => {
    return (
      <Stack gap='xs'>
        {output?.pk && (
          <Stack gap='xs'>
            <Alert
              color='blue'
              icon={<IconInfoCircle />}
              title={t`Build Output`}
            >
              <RenderStockItem instance={output} />
            </Alert>
            <Divider />
          </Stack>
        )}
        <StandaloneField fieldDefinition={sourceLocationField} />
      </Stack>
    );
  }, [output, sourceLocationField]);

  return useCreateApiFormModal({
    url: ApiEndpoints.build_order_allocate,
    pk: buildId,
    title: t`Allocate Stock`,
    fields: buildAllocateFields,
    preFormContent: preFormContent,
    successMessage: t`Stock items allocated`,
    onFormSuccess: onFormSuccess,
    initialData: {
      items: lineItems.map((item) => {
        return {
          build_line: item.pk,
          stock_item: undefined,
          quantity: Math.max(0, item.requiredQuantity - item.allocatedQuantity),
          output: outputId
        };
      })
    },
    size: '80%'
  });
}
