import { t } from '@lingui/macro';
import { Table } from '@mantine/core';
import { useMemo } from 'react';

import RemoveRowButton from '../components/buttons/RemoveRowButton';
import { StandaloneField } from '../components/forms/StandaloneField';
import type {
  ApiFormFieldSet,
  ApiFormFieldType
} from '../components/forms/fields/ApiFormField';
import type { TableFieldRowProps } from '../components/forms/fields/TableField';

function BuildAllocateLineRow({
  props
}: Readonly<{
  props: TableFieldRowProps;
}>) {
  const valueField: ApiFormFieldType = useMemo(() => {
    return {
      field_type: 'string',
      name: 'value',
      required: true,
      value: props.item.value,
      onValueChange: (value: any) => {
        props.changeFn(props.idx, 'value', value);
      }
    };
  }, [props]);

  const labelField: ApiFormFieldType = useMemo(() => {
    return {
      field_type: 'string',
      name: 'label',
      required: true,
      value: props.item.label,
      onValueChange: (value: any) => {
        props.changeFn(props.idx, 'label', value);
      }
    };
  }, [props]);

  const descriptionField: ApiFormFieldType = useMemo(() => {
    return {
      field_type: 'string',
      name: 'description',
      required: true,
      value: props.item.description,
      onValueChange: (value: any) => {
        props.changeFn(props.idx, 'description', value);
      }
    };
  }, [props]);

  const activeField: ApiFormFieldType = useMemo(() => {
    return {
      field_type: 'boolean',
      name: 'active',
      required: true,
      value: props.item.active,
      onValueChange: (value: any) => {
        props.changeFn(props.idx, 'active', value);
      }
    };
  }, [props]);

  return (
    <Table.Tr key={`table-row-${props.item.pk}`}>
      <Table.Td>
        <StandaloneField fieldName='value' fieldDefinition={valueField} />
      </Table.Td>
      <Table.Td>
        <StandaloneField fieldName='label' fieldDefinition={labelField} />
      </Table.Td>
      <Table.Td>
        <StandaloneField
          fieldName='description'
          fieldDefinition={descriptionField}
        />
      </Table.Td>
      <Table.Td>
        <StandaloneField fieldName='active' fieldDefinition={activeField} />
      </Table.Td>
      <Table.Td>
        <RemoveRowButton onClick={() => props.removeFn(props.idx)} />
      </Table.Td>
    </Table.Tr>
  );
}

export function selectionListFields(): ApiFormFieldSet {
  return {
    name: {},
    description: {},
    active: {},
    locked: {},
    source_plugin: {},
    source_string: {},
    choices: {
      label: t`Entries`,
      description: t`List of entries to choose from`,
      field_type: 'table',
      value: [],
      headers: [t`Value`, t`Label`, t`Description`, t`Active`],
      modelRenderer: (row: TableFieldRowProps) => (
        <BuildAllocateLineRow props={row} />
      ),
      addRow: () => {
        return {
          value: '',
          label: '',
          description: '',
          active: true
        };
      }
    }
  };
}
