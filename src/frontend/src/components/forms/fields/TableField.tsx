import { Trans, t } from '@lingui/macro';
import { Table } from '@mantine/core';
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
    console.log('Changing', idx, key, value);
    const val = field.value;
    console.log('Was', val[idx][key]);
    console.log('All:', field.value);
    val[idx][key] = value;
    field.onChange(val);
  };

  const removeRow = (idx: number) => {
    const val = field.value;
    val.splice(idx, 1);
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
        {value.length > 0 ? (
          value.map((item: any, idx: number) => {
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
          })
        ) : (
          <tr>
            <td
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
            </td>
          </tr>
        )}
      </tbody>
    </Table>
  );
}
