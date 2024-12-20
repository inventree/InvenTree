import { Trans, t } from '@lingui/macro';
import { Alert, Container, Group, Stack, Table, Text } from '@mantine/core';
import { IconExclamationCircle } from '@tabler/icons-react';
import { type ReactNode, useCallback, useEffect, useMemo } from 'react';
import type { FieldValues, UseControllerReturn } from 'react-hook-form';

import { identifierString } from '../../../functions/conversion';
import { InvenTreeIcon } from '../../../functions/icons';
import { AddItemButton } from '../../buttons/AddItemButton';
import { StandaloneField } from '../StandaloneField';
import type { ApiFormFieldType } from './ApiFormField';

export interface TableFieldRowProps {
  item: any;
  idx: number;
  rowErrors: any;
  control: UseControllerReturn<FieldValues, any>;
  changeFn: (idx: number, key: string, value: any) => void;
  removeFn: (idx: number) => void;
}

function TableFieldRow({
  item,
  idx,
  errors,
  definition,
  control,
  changeFn,
  removeFn
}: Readonly<{
  item: any;
  idx: number;
  errors: any;
  definition: ApiFormFieldType;
  control: UseControllerReturn<FieldValues, any>;
  changeFn: (idx: number, key: string, value: any) => void;
  removeFn: (idx: number) => void;
}>) {
  // Table fields require render function
  if (!definition.modelRenderer) {
    return (
      <Table.Tr key='table-row-no-renderer'>
        <Table.Td colSpan={definition.headers?.length}>
          <Alert color='red' title={t`Error`} icon={<IconExclamationCircle />}>
            {t`modelRenderer entry required for tables`}
          </Alert>
        </Table.Td>
      </Table.Tr>
    );
  }

  return definition.modelRenderer({
    item: item,
    idx: idx,
    rowErrors: errors,
    control: control,
    changeFn: changeFn,
    removeFn: removeFn
  });
}

export function TableFieldErrorWrapper({
  props,
  errorKey,
  children
}: Readonly<{
  props: TableFieldRowProps;
  errorKey: string;
  children: ReactNode;
}>) {
  const msg = props?.rowErrors?.[errorKey];

  return (
    <Stack gap='xs'>
      {children}
      {msg && (
        <Text size='xs' c='red'>
          {msg.message}
        </Text>
      )}
    </Stack>
  );
}

export function TableField({
  definition,
  fieldName,
  control
}: Readonly<{
  definition: ApiFormFieldType;
  fieldName: string;
  control: UseControllerReturn<FieldValues, any>;
}>) {
  const {
    field,
    fieldState: { error }
  } = control;
  const { value } = field;

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

  const fieldDefinition = useMemo(() => {
    return {
      ...definition,
      modelRenderer: undefined,
      onValueChange: undefined,
      adjustFilters: undefined,
      read_only: undefined,
      addRow: undefined
    };
  }, [definition]);

  // Extract errors associated with the current row
  const rowErrors: any = useCallback(
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
          {definition.headers?.map((header, index) => {
            return (
              <Table.Th
                key={`table-header-${identifierString(header)}-${index}`}
              >
                {header}
              </Table.Th>
            );
          })}
        </Table.Tr>
      </Table.Thead>

      <Table.Tbody>
        {value.length > 0 ? (
          value.map((item: any, idx: number) => {
            return (
              <TableFieldRow
                key={`table-row-${idx}`}
                item={item}
                idx={idx}
                errors={rowErrors(idx)}
                control={control}
                definition={definition}
                changeFn={onRowFieldChange}
                removeFn={removeRow}
              />
            );
          })
        ) : (
          <Table.Tr key='table-row-no-entries'>
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
                <InvenTreeIcon icon='info' />
                <Trans>No entries available</Trans>
              </span>
            </Table.Td>
          </Table.Tr>
        )}
      </Table.Tbody>
      {definition.addRow && (
        <Table.Tfoot>
          <Table.Tr>
            <Table.Td colSpan={definition.headers?.length}>
              <AddItemButton
                tooltip={t`Add new row`}
                onClick={() => {
                  if (definition.addRow === undefined) return;
                  const ret = definition.addRow();
                  if (ret) {
                    const val = field.value;
                    val.push(ret);
                    field.onChange(val);
                  }
                }}
              />
            </Table.Td>
          </Table.Tr>
        </Table.Tfoot>
      )}
    </Table>
  );
}

/*
 * Display an "extra" row below the main table row, for additional information.
 * - Each "row" can display an extra row of information below the main row
 */
export function TableFieldExtraRow({
  visible,
  fieldName,
  fieldDefinition,
  defaultValue,
  emptyValue,
  error,
  onValueChange
}: {
  visible: boolean;
  fieldName?: string;
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
          <Group grow preventGrowOverflow={false} justify='flex-apart' p='xs'>
            <Container flex={0} p='xs'>
              <InvenTreeIcon icon='downright' />
            </Container>
            <StandaloneField
              fieldName={fieldName ?? 'field'}
              fieldDefinition={field}
              defaultValue={defaultValue}
              error={fieldDefinition.error ?? error}
            />
          </Group>
        </Table.Td>
      </Table.Tr>
    )
  );
}
