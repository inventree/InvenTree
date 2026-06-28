import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import { Alert, Container, Group, Stack, Table, Text } from '@mantine/core';
import { IconExclamationCircle } from '@tabler/icons-react';
import {
  type ReactNode,
  memo,
  useCallback,
  useEffect,
  useMemo,
  useRef
} from 'react';

import { AddItemButton } from '@lib/components/AddItemButton';
import { identifierString } from '@lib/functions/Conversion';
import type { ApiFormFieldType } from '@lib/types/Forms';
import { useWhyDidYouUpdate } from '../../../functions/debug';
import { InvenTreeIcon } from '../../../functions/icons';
import { StandaloneField } from '../StandaloneField';

export interface TableFieldRowProps {
  item: any;
  idx: number;
  rowId: string | number;
  rowErrors: any;
  changeFn: (idx: number | string, key: string, value: any) => void;
  removeFn: (idx: number | string) => void;
}

function TableFieldRow({
  item,
  rowId,
  errors,
  definition,
  changeFn,
  removeFn
}: Readonly<{
  item: any;
  rowId: string | number;
  errors: any;
  definition: ApiFormFieldType;
  changeFn: (idx: number, key: string, value: any) => void;
  removeFn: (idx: number | string) => void;
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
    rowId: rowId,
    rowErrors: errors,
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

function TableFieldComponent({
  definition,
  fieldName,
  value,
  onChange,
  error
}: Readonly<{
  definition: ApiFormFieldType;
  fieldName: string;
  value: any;
  onChange: (value: any) => void;
  error?: any;
}>) {
  const valueRef = useRef(value);
  const onChangeRef = useRef(onChange);
  const rowIndexByIdRef = useRef(new Map<string | number, number>());
  const generatedRowIdsRef = useRef(new WeakMap<object, string>());
  const generatedRowIdCounterRef = useRef(0);

  const getRowIdentifier = useCallback(
    (item: any, idx: number): string | number => {
      if (item && typeof item === 'object') {
        const intrinsicId = item.pk ?? item.item ?? item.id ?? item.uuid;

        if (intrinsicId !== undefined && intrinsicId !== null) {
          return intrinsicId;
        }

        const existingGeneratedId = generatedRowIdsRef.current.get(item);

        if (existingGeneratedId) {
          return existingGeneratedId;
        }

        generatedRowIdCounterRef.current += 1;
        const generatedId = `table-row-generated-${generatedRowIdCounterRef.current}`;
        generatedRowIdsRef.current.set(item, generatedId);

        return generatedId;
      }

      return item ?? idx;
    },
    []
  );

  // Keep refs in sync with latest values without introducing them as deps
  valueRef.current = value;
  onChangeRef.current = onChange;

  useEffect(() => {
    const nextRowIndexById = new Map<string | number, number>();

    value?.forEach((item: any, idx: number) => {
      nextRowIndexById.set(getRowIdentifier(item, idx), idx);
    });

    rowIndexByIdRef.current = nextRowIndexById;
  }, [value, getRowIdentifier]);

  const resolveRowIndex = useCallback((identifier: number | string) => {
    const mappedIndex = rowIndexByIdRef.current.get(identifier);

    if (mappedIndex !== undefined) {
      return mappedIndex;
    }

    if (typeof identifier === 'number' && identifier >= 0) {
      return identifier;
    }

    return undefined;
  }, []);

  const onRowFieldChange = useCallback(
    (identifier: number | string, key: string, rowValue: any) => {
      const idx = resolveRowIndex(identifier);

      if (idx === undefined) {
        return;
      }

      const currentValue = valueRef.current;

      if (!Array.isArray(currentValue) || currentValue[idx] === undefined) {
        return;
      }

      const nextValue = [...currentValue];
      const currentRow = nextValue[idx];

      if (currentRow && typeof currentRow === 'object') {
        nextValue[idx] = {
          ...currentRow,
          [key]: rowValue
        };
      }

      onChangeRef.current(nextValue);
    },
    [resolveRowIndex]
  );

  const removeRow = useCallback(
    (identifier: number | string) => {
      const idx = resolveRowIndex(identifier);

      if (idx === undefined) {
        return;
      }

      const currentValue = valueRef.current;

      if (!Array.isArray(currentValue)) {
        return;
      }

      const nextValue = [...currentValue];
      nextValue.splice(idx, 1);

      onChangeRef.current(nextValue);
    },
    [resolveRowIndex]
  );

  // Extract errors associated with the current row
  const rowErrors: any = useCallback(
    (idx: number) => {
      if (Array.isArray(error)) {
        return error[idx];
      }
    },
    [error]
  );

  useWhyDidYouUpdate(`TableField-${fieldName}`, {
    definition,
    fieldName,
    value,
    error
  });

  return (
    <Table
      highlightOnHover
      striped
      aria-label={`table-field-${fieldName}`}
      style={{ width: '100%' }}
    >
      <Table.Thead>
        <Table.Tr>
          {definition.headers?.map((header, index) => {
            return (
              <Table.Th
                key={`table-header-${identifierString(header.title)}`}
                style={header.style}
              >
                {header.title}
              </Table.Th>
            );
          })}
        </Table.Tr>
      </Table.Thead>

      <Table.Tbody>
        {(value?.length ?? 0) > 0 ? (
          value.map((item: any, idx: number) => {
            const rowId = getRowIdentifier(item, idx);

            return (
              <TableFieldRow
                key={`table-row-${rowId}`}
                item={item}
                rowId={rowId}
                errors={rowErrors(idx)}
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
                    onChange([...(value ?? []), ret]);
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

export const TableField = memo(
  TableFieldComponent,
  (previousProps, nextProps) => {
    return (
      previousProps.definition === nextProps.definition &&
      previousProps.fieldName === nextProps.fieldName &&
      previousProps.value === nextProps.value &&
      previousProps.onChange === nextProps.onChange &&
      previousProps.error === nextProps.error
    );
  }
);

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
  const hasMounted = useRef(false);

  // Callback whenever the visibility of the sub-field changes
  // Skip the initial mount — the value was never set, nothing to reset
  useEffect(() => {
    if (!hasMounted.current) {
      hasMounted.current = true;
      return;
    }
    if (!visible) {
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
