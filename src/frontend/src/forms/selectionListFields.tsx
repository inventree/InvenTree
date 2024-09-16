import { t } from '@lingui/macro';
import { Table } from '@mantine/core';

import { ApiFormFieldSet } from '../components/forms/fields/ApiFormField';
import { TableFieldRowProps } from '../components/forms/fields/TableField';

export function selectionRenderer(row: TableFieldRowProps) {
  const item = row.item;
  return (
    <Table.Tr key={item.pk}>
      <Table.Td>
        <strong>{item.value}</strong>
      </Table.Td>
      <Table.Td>{item.label}</Table.Td>
      <Table.Td>{item.description}</Table.Td>
      <Table.Td>{item.active ? 'Active' : 'Inactive'}</Table.Td>
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
      modelRenderer: selectionRenderer
    }
  };
}
