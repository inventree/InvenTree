import { t } from '@lingui/macro';
import { Alert, Stack, Table, Text } from '@mantine/core';
import {
  IconCalendar,
  IconLink,
  IconList,
  IconSitemap,
  IconTruckDelivery,
  IconUser,
  IconUsersGroup
} from '@tabler/icons-react';
import { DataTable } from 'mantine-datatable';
import { useEffect, useMemo, useState } from 'react';
import { useFormContext } from 'react-hook-form';

import { api } from '../App';
import { ActionButton } from '../components/buttons/ActionButton';
import RemoveRowButton from '../components/buttons/RemoveRowButton';
import { StandaloneField } from '../components/forms/StandaloneField';
import {
  ApiFormFieldSet,
  ApiFormFieldType
} from '../components/forms/fields/ApiFormField';
import { TableFieldRowProps } from '../components/forms/fields/TableField';
import { ProgressBar } from '../components/items/ProgressBar';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { ModelType } from '../enums/ModelType';
import { resolveItem } from '../functions/conversion';
import { InvenTreeIcon } from '../functions/icons';
import { useCreateApiFormModal } from '../hooks/UseForm';
import { useBatchCodeGenerator } from '../hooks/UseGenerator';
import { useSelectedRows } from '../hooks/UseSelectedRows';
import { apiUrl } from '../states/ApiState';
import { useGlobalSettingsState } from '../states/SettingsState';
import { PartColumn, StatusColumn } from '../tables/ColumnRenderers';

/**
 * Field set for BuildOrder forms
 */
export function useBuildOrderFields({
  create
}: {
  create: boolean;
}): ApiFormFieldSet {
  const [destination, setDestination] = useState<number | null | undefined>(
    null
  );

  const [batchCode, setBatchCode] = useState<string>('');

  const batchGenerator = useBatchCodeGenerator((value: any) => {
    if (!batchCode) {
      setBatchCode(value);
    }
  });

  const globalSettings = useGlobalSettingsState();

  return useMemo(() => {
    let fields: ApiFormFieldSet = {
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
        value: batchCode,
        onValueChange: (value: any) => setBatchCode(value)
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
      }
    };

    if (create) {
      fields.create_child_builds = {};
    }

    return fields;
  }, [create, destination, batchCode, globalSettings]);
}

export function useBuildOrderOutputFields({
  build
}: {
  build: any;
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
    let build_quantity = build.quantity ?? 0;
    let build_complete = build.completed ?? 0;

    setQuantity(Math.max(0, build_quantity - build_complete));
  }, [build]);

  const [serialPlaceholder, setSerialPlaceholder] = useState<string>('');

  useEffect(() => {
    if (trackable) {
      api
        .get(apiUrl(ApiEndpoints.part_serial_numbers, build.part_detail.pk))
        .then((response: any) => {
          if (response.data?.next) {
            setSerialPlaceholder(
              t`Next serial number` + ' - ' + response.data.next
            );
          } else if (response.data?.latest) {
            setSerialPlaceholder(
              t`Latest serial number` + ' - ' + response.data.latest
            );
          } else {
            setSerialPlaceholder('');
          }
        })
        .catch(() => {
          setSerialPlaceholder('');
        });
    } else {
      setSerialPlaceholder('');
    }
  }, [build, trackable]);

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
        placeholder: serialPlaceholder
      },
      batch_code: {},
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
  }, [quantity, serialPlaceholder, trackable]);
}

/*
 * Construct a table of build outputs, for displaying at the top of a form
 */
function buildOutputFormTable(outputs: any[], onRemove: (output: any) => void) {
  return (
    <DataTable
      idAccessor="pk"
      records={outputs}
      columns={[
        {
          accessor: 'part',
          title: t`Part`,
          render: (record: any) => PartColumn(record.part_detail)
        },
        {
          accessor: 'quantity',
          title: t`Quantity`,
          render: (record: any) => {
            if (record.serial) {
              return `# ${record.serial}`;
            } else {
              return record.quantity;
            }
          }
        },
        StatusColumn({ model: ModelType.stockitem, sortable: false }),
        {
          accessor: 'actions',
          title: '',
          render: (record: any) => (
            <ActionButton
              key={`remove-output-${record.pk}`}
              tooltip={t`Remove output`}
              icon={<InvenTreeIcon icon="cancel" />}
              color="red"
              onClick={() => onRemove(record.pk)}
              disabled={outputs.length <= 1}
            />
          )
        }
      ]}
    />
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

  const { selectedRows, removeRow } = useSelectedRows({
    rows: outputs
  });

  useEffect(() => {
    if (location) {
      return;
    }

    setLocation(
      build.destination || build.part_detail?.default_location || null
    );
  }, [location, build.destination, build.part_detail]);

  const preFormContent = useMemo(() => {
    return buildOutputFormTable(selectedRows, removeRow);
  }, [selectedRows, removeRow]);

  const buildOutputCompleteFields: ApiFormFieldSet = useMemo(() => {
    return {
      outputs: {
        hidden: true,
        value: selectedRows.map((output: any) => {
          return {
            output: output.pk
          };
        })
      },
      status_custom_key: {},
      location: {
        filters: {
          structural: false
        },
        value: location,
        onValueChange: (value) => {
          setLocation(value);
        }
      },
      notes: {},
      accept_incomplete_allocation: {}
    };
  }, [selectedRows, location]);

  return useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.build_output_complete, build.pk),
    method: 'POST',
    title: t`Complete Build Outputs`,
    fields: buildOutputCompleteFields,
    onFormSuccess: onFormSuccess,
    preFormContent: preFormContent,
    successMessage: t`Build outputs have been completed`
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

  const { selectedRows, removeRow } = useSelectedRows({
    rows: outputs
  });

  useEffect(() => {
    if (location) {
      return;
    }

    setLocation(
      build.destination || build.part_detail?.default_location || null
    );
  }, [location, build.destination, build.part_detail]);

  const preFormContent = useMemo(() => {
    return buildOutputFormTable(selectedRows, removeRow);
  }, [selectedRows, removeRow]);

  const buildOutputScrapFields: ApiFormFieldSet = useMemo(() => {
    return {
      outputs: {
        hidden: true,
        value: selectedRows.map((output: any) => {
          return {
            output: output.pk,
            quantity: output.quantity
          };
        })
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
  }, [location, selectedRows]);

  return useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.build_output_scrap, build.pk),
    method: 'POST',
    title: t`Scrap Build Outputs`,
    fields: buildOutputScrapFields,
    onFormSuccess: onFormSuccess,
    preFormContent: preFormContent,
    successMessage: t`Build outputs have been scrapped`
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
  const { selectedRows, removeRow } = useSelectedRows({
    rows: outputs
  });

  const preFormContent = useMemo(() => {
    return (
      <Stack gap="xs">
        <Alert color="red" title={t`Cancel Build Outputs`}>
          <Text>{t`Selected build outputs will be deleted`}</Text>
        </Alert>
        {buildOutputFormTable(selectedRows, removeRow)}
      </Stack>
    );
  }, [selectedRows, removeRow]);

  const buildOutputCancelFields: ApiFormFieldSet = useMemo(() => {
    return {
      outputs: {
        hidden: true,
        value: selectedRows.map((output: any) => {
          return {
            output: output.pk
          };
        })
      }
    };
  }, [selectedRows]);

  return useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.build_output_delete, build.pk),
    method: 'POST',
    title: t`Cancel Build Outputs`,
    fields: buildOutputCancelFields,
    preFormContent: preFormContent,
    onFormSuccess: onFormSuccess,
    successMessage: t`Build outputs have been cancelled`
  });
}

function buildAllocationFormTable(
  outputs: any[],
  onRemove: (output: any) => void
) {
  return (
    <DataTable
      idAccessor="pk"
      records={outputs}
      columns={[
        {
          accessor: 'part',
          title: t`Part`,
          render: (record: any) => PartColumn(record.part_detail)
        },
        {
          accessor: 'allocated',
          title: t`Allocated`,
          render: (record: any) => (
            <ProgressBar
              value={record.allocated}
              maximum={record.quantity}
              progressLabel
            />
          )
        },
        {
          accessor: 'actions',
          title: '',
          render: (record: any) => (
            <ActionButton
              key={`remove-line-${record.pk}`}
              tooltip={t`Remove line`}
              icon={<InvenTreeIcon icon="cancel" />}
              color="red"
              onClick={() => onRemove(record.pk)}
              disabled={outputs.length <= 1}
            />
          )
        }
      ]}
    />
  );
}

// Construct a single row in the 'allocate stock to build' table
function BuildAllocateLineRow({
  props,
  record,
  sourceLocation
}: {
  props: TableFieldRowProps;
  record: any;
  sourceLocation: number | undefined;
}) {
  const stockField: ApiFormFieldType = useMemo(() => {
    return {
      field_type: 'related field',
      api_url: apiUrl(ApiEndpoints.stock_item_list),
      model: ModelType.stockitem,
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
          let available = instance.quantity - instance.allocated;

          props.changeFn(
            props.idx,
            'quantity',
            Math.min(props.item.quantity, available)
          );
        }
      }
    };
  }, [props]);

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

  const partDetail = useMemo(
    () => PartColumn(record.part_detail),
    [record.part_detail]
  );

  return (
    <>
      <Table.Tr key={`table-row-${record.pk}`}>
        <Table.Td>{partDetail}</Table.Td>
        <Table.Td>
          <ProgressBar
            value={record.allocated}
            maximum={record.quantity}
            progressLabel
          />
        </Table.Td>
        <Table.Td>
          <StandaloneField
            fieldName="stock_item"
            fieldDefinition={stockField}
            error={props.rowErrors?.stock_item?.message}
          />
        </Table.Td>
        <Table.Td>
          <StandaloneField
            fieldName="quantity"
            fieldDefinition={quantityField}
            error={props.rowErrors?.quantity?.message}
          />
        </Table.Td>
        <Table.Td>
          <RemoveRowButton onClick={() => props.removeFn(props.idx)} />
        </Table.Td>
      </Table.Tr>
    </>
  );
}

/*
 * Dynamic form for allocating stock against multiple build order line items
 */
export function useAllocateStockToBuildForm({
  buildId,
  outputId,
  build,
  lineItems,
  onFormSuccess
}: {
  buildId: number;
  outputId?: number | null;
  build: any;
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
        headers: [t`Part`, t`Allocated`, t`Stock Item`, t`Quantity`],
        modelRenderer: (row: TableFieldRowProps) => {
          // Find the matching record from the passed 'lineItems'
          const record =
            lineItems.find((item) => item.pk == row.item.build_line) ?? {};
          return (
            <BuildAllocateLineRow
              props={row}
              record={record}
              sourceLocation={sourceLocation}
            />
          );
        }
      }
    };

    return fields;
  }, [lineItems, sourceLocation]);

  useEffect(() => {
    setSourceLocation(build.take_from);
  }, [build.take_from]);

  const sourceLocationField: ApiFormFieldType = useMemo(() => {
    return {
      field_type: 'related field',
      api_url: apiUrl(ApiEndpoints.stock_location_list),
      model: ModelType.stocklocation,
      required: false,
      label: t`Source Location`,
      description: t`Select the source location for the stock allocation`,
      name: 'source_location',
      value: build.take_from,
      onValueChange: (value: any) => {
        setSourceLocation(value);
      }
    };
  }, [build?.take_from]);

  const preFormContent = useMemo(() => {
    return (
      <Stack gap="xs">
        <StandaloneField fieldDefinition={sourceLocationField} />
      </Stack>
    );
  }, [sourceLocationField]);

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
          quantity: Math.max(0, item.quantity - item.allocated),
          output: null
        };
      })
    },
    size: '80%'
  });
}
