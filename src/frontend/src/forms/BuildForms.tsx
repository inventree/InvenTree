import { t } from '@lingui/macro';
import { ActionIcon, Alert, Stack, Text } from '@mantine/core';
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
import { useCallback, useEffect, useMemo, useState } from 'react';

import { api } from '../App';
import { ActionButton } from '../components/buttons/ActionButton';
import { ApiFormFieldSet } from '../components/forms/fields/ApiFormField';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { ModelType } from '../enums/ModelType';
import { InvenTreeIcon } from '../functions/icons';
import { useCreateApiFormModal } from '../hooks/UseForm';
import { useBatchCodeGenerator } from '../hooks/UseGenerator';
import { apiUrl } from '../states/ApiState';
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

  return useMemo(() => {
    return {
      reference: {},
      part: {
        disabled: !create,
        filters: {
          assembly: true,
          virtual: false
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
        icon: <IconUser />
      },
      responsible: {
        icon: <IconUsersGroup />,
        filters: {
          is_active: true
        }
      }
    };
  }, [create, destination, batchCode]);
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
              onClick={() => onRemove(record)}
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
  const [selectedOutputs, setSelectedOutputs] = useState<any[]>([]);

  const [location, setLocation] = useState<number | null>(null);

  useEffect(() => {
    setSelectedOutputs(outputs);
  }, [outputs]);

  useEffect(() => {
    if (location) {
      return;
    }

    setLocation(
      build.destination || build.part_detail?.default_location || null
    );
  }, [location, build.destination, build.part_detail]);

  // Remove a selected output from the list
  const removeOutput = useCallback(
    (output: any) => {
      setSelectedOutputs(
        selectedOutputs.filter((item) => item.pk != output.pk)
      );
    },
    [selectedOutputs]
  );

  const preFormContent = useMemo(() => {
    return buildOutputFormTable(selectedOutputs, removeOutput);
  }, [selectedOutputs, removeOutput]);

  const buildOutputCompleteFields: ApiFormFieldSet = useMemo(() => {
    return {
      outputs: {
        hidden: true,
        value: selectedOutputs.map((output) => {
          return {
            output: output.pk
          };
        })
      },
      status: {},
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
  }, [selectedOutputs, location]);

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
  const [selectedOutputs, setSelectedOutputs] = useState<any[]>([]);

  useEffect(() => {
    setSelectedOutputs(outputs);
  }, [outputs]);

  // Remove a selected output from the list
  const removeOutput = useCallback(
    (output: any) => {
      setSelectedOutputs(
        selectedOutputs.filter((item) => item.pk != output.pk)
      );
    },
    [selectedOutputs]
  );

  useEffect(() => {
    if (location) {
      return;
    }

    setLocation(
      build.destination || build.part_detail?.default_location || null
    );
  }, [location, build.destination, build.part_detail]);

  const preFormContent = useMemo(() => {
    return buildOutputFormTable(selectedOutputs, removeOutput);
  }, [selectedOutputs, removeOutput]);

  const buildOutputScrapFields: ApiFormFieldSet = useMemo(() => {
    return {
      outputs: {
        hidden: true,
        value: selectedOutputs.map((output) => {
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
  }, [location, selectedOutputs]);

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
  const [selectedOutputs, setSelectedOutputs] = useState<any[]>([]);

  useEffect(() => {
    setSelectedOutputs(outputs);
  }, [outputs]);

  // Remove a selected output from the list
  const removeOutput = useCallback(
    (output: any) => {
      setSelectedOutputs(
        selectedOutputs.filter((item) => item.pk != output.pk)
      );
    },
    [selectedOutputs]
  );

  const preFormContent = useMemo(() => {
    return (
      <Stack gap="xs">
        <Alert color="red" title={t`Cancel Build Outputs`}>
          <Text>{t`Selected build outputs will be deleted`}</Text>
        </Alert>
        {buildOutputFormTable(selectedOutputs, removeOutput)}
      </Stack>
    );
  }, [selectedOutputs, removeOutput]);

  const buildOutputCancelFields: ApiFormFieldSet = useMemo(() => {
    return {
      outputs: {
        hidden: true,
        value: selectedOutputs.map((output) => {
          return {
            output: output.pk
          };
        })
      }
    };
  }, [selectedOutputs]);

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
