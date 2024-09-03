import { Trans, t } from '@lingui/macro';
import { Container, Group, Table } from '@mantine/core';
import { useCallback, useEffect, useMemo } from 'react';
import { FieldValues, UseControllerReturn } from 'react-hook-form';

import { InvenTreeIcon } from '../../../functions/icons';
import { StandaloneField } from '../StandaloneField';
import { ApiFormFieldType } from './ApiFormField';

export interface TableFieldRowProps {
  item: any;
  idx: number;
  rowErrors: any;
  control: UseControllerReturn<FieldValues, any>;
  changeFn: (idx: number, key: string, value: any) => void;
  removeFn: (idx: number) => void;
}

export function TableField({
  definition,
  fieldName,
  control
}: {
  definition: ApiFormFieldType;
  fieldName: string;
  control: UseControllerReturn<FieldValues, any>;
}) {
  const {
    field,
    fieldState: { error }
  } = control;
  const { value, ref } = field;

  const onRowFieldChange = (idx: number, key: string, value: any) => {
    const val = field.value;
    val[idx][key] = value;

    field.onChange(val);
  };

  const removeRow = (idx: number) => {
    const val = field.value;
    val.splice(idx, 1);
    field.onChange(val);
  };

  // Extract errors associated with the current row
  const rowErrors = useCallback(
    (idx: number) => {
      if (Array.isArray(error)) {
        return error[idx];
      }
    },
    [error]
  );

  return (
    <Table highlightOnHover striped aria-label={`table-field-${field.name}`}>
      <Table.Thead>
        <Table.Tr>
          {definition.headers?.map((header) => {
            return <Table.Th key={header}>{header}</Table.Th>;
          })}
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {value.length > 0 ? (
          value.map((item: any, idx: number) => {
            // Table fields require render function
            if (!definition.modelRenderer) {
              return (
                <Table.Tr key="table-row-no-renderer">{t`modelRenderer entry required for tables`}</Table.Tr>
              );
            }

            return definition.modelRenderer({
              item: item,
              idx: idx,
              rowErrors: rowErrors(idx),
              control: control,
              changeFn: onRowFieldChange,
              removeFn: removeRow
            });
          })
        ) : (
          <Table.Tr key="table-row-no-entries">
            <Table.Td
              style={{ textAlign: 'center' }}
              colSpan={definition.headers?.length}
            >
              <span
                style={{
                  display: 'flex',
                  justifyContent: 'center',
                  gap: '5px'
                }}
              >
                <InvenTreeIcon icon="info" />
                <Trans>No entries available</Trans>
              </span>
            </Table.Td>
          </Table.Tr>
        )}
      </Table.Tbody>
    </Table>
  );
}

/*
 * Display an "extra" row below the main table row, for additional information.
 * - Each "row" can display an extra row of information below the main row
 */
export function TableFieldExtraRow({
  visible,
  fieldDefinition,
  defaultValue,
  emptyValue,
  error,
  onValueChange
}: {
  visible: boolean;
  fieldDefinition: ApiFormFieldType;
  defaultValue?: any;
  error?: string;
  emptyValue?: any;
  onValueChange: (value: any) => void;
}) {
  // Callback whenever the visibility of the sub-field changes
  useEffect(() => {
    if (!visible) {
      // If the sub-field is hidden, reset the value to the "empty" value
      onValueChange(emptyValue);
    }
  }, [visible]);

  const field: ApiFormFieldType = useMemo(() => {
    return {
      ...fieldDefinition,
      default: defaultValue,
      onValueChange: (value: any) => {
        onValueChange(value);
      }
    };
  }, [fieldDefinition]);

  return (
    visible && (
      <Table.Tr>
        <Table.Td colSpan={10}>
          <Group grow preventGrowOverflow={false} justify="flex-apart" p="xs">
            <Container flex={0} p="xs">
              <InvenTreeIcon icon="downright" />
            </Container>
            <StandaloneField
              fieldDefinition={field}
              defaultValue={defaultValue}
              error={error}
            />
          </Group>
        </Table.Td>
      </Table.Tr>
    )
  );
}
