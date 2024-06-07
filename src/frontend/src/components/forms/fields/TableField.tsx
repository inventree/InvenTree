import { Trans, t } from '@lingui/macro';
import { Container, Flex, Group, Table } from '@mantine/core';
import { FieldValues, UseControllerReturn } from 'react-hook-form';

import { InvenTreeIcon } from '../../../functions/icons';
import { ApiFormFieldType } from './ApiFormField';

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
                <Table.Tr>{t`modelRenderer entry required for tables`}</Table.Tr>
              );
            }
            return definition.modelRenderer({
              item: item,
              idx: idx,
              changeFn: onRowFieldChange,
              removeFn: removeRow
            });
          })
        ) : (
          <Table.Tr>
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
 */
export function TableFieldExtraRow({
  visible,
  content,
  colSpan
}: {
  visible: boolean;
  content: React.ReactNode;
  colSpan?: number;
}) {
  return (
    visible && (
      <Table.Tr>
        <Table.Td colSpan={colSpan ?? 3}>
          <Group justify="flex-start" grow>
            <InvenTreeIcon icon="downright" />
            {content}
          </Group>
        </Table.Td>
      </Table.Tr>
    )
  );
}
