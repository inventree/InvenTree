import { t } from '@lingui/macro';
import { Table } from '@mantine/core';
import { useCallback } from 'react';
import { FieldValues, UseControllerReturn } from 'react-hook-form';

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
    val[idx] = undefined;
    field.onChange(val);
  };

  return (
    <Table highlightOnHover striped>
      <thead>
        <tr>
          {definition.headers?.map((header) => {
            return <th key={header}>{header}</th>;
          })}
        </tr>
      </thead>
      <tbody>
        {value.map((item: any, idx: number) => {
          // Item was removed from table by user
          if (!item) {
            return;
          }

          // Table fields require render function
          if (!definition.modelRenderer) {
            return <tr>{t`modelRenderer entry required for tables`}</tr>;
          }
          return definition.modelRenderer({
            item: item,
            idx: idx,
            changeFn: onRowFieldChange,
            removeFn: removeRow
          });
        })}
      </tbody>
    </Table>
  );
}
