import { t } from '@lingui/macro';
import { ActionIcon, Checkbox, Menu, Tooltip } from '@mantine/core';
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
          <Tooltip label={t`Select Columns`}>
            <IconAdjustments />
          </Tooltip>
        </ActionIcon>
      </Menu.Target>

      <Menu.Dropdown>
        <Menu.Label>{t`Select Columns`}</Menu.Label>
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
