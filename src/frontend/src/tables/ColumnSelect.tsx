import { t } from '@lingui/core/macro';
import { ActionIcon, Checkbox, Divider, Menu, Tooltip } from '@mantine/core';
import { IconAdjustments } from '@tabler/icons-react';

export function TableColumnSelect({
  columns,
  onToggleColumn
}: Readonly<{
  columns: any[];
  onToggleColumn: (columnName: string) => void;
}>) {
  return (
    <Menu shadow='xs' closeOnItemClick={false}>
      <Menu.Target>
        <ActionIcon variant='transparent' aria-label='table-select-columns'>
          <Tooltip label={t`Select Columns`} position='top-end'>
            <IconAdjustments />
          </Tooltip>
        </ActionIcon>
      </Menu.Target>

      <Menu.Dropdown style={{ maxHeight: '400px', overflowY: 'auto' }}>
        <Menu.Label>{t`Select Columns`}</Menu.Label>
        <Divider />
        {columns
          .filter((col) => col.switchable ?? true)
          .map((col) => (
            <Menu.Item key={col.accessor}>
              <Checkbox
                checked={!col.hidden}
                label={col.title || col.accessor}
                onChange={() => onToggleColumn(col.accessor)}
                radius='sm'
              />
            </Menu.Item>
          ))}
      </Menu.Dropdown>
    </Menu>
  );
}
