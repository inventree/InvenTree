import { t } from '@lingui/macro';
import { Checkbox, Menu, Tooltip } from '@mantine/core';
import { ActionIcon } from '@mantine/core';
import { IconAdjustments } from '@tabler/icons-react';

export function TableColumnSelect({
  columns,
  onToggleColumn
}: {
  columns: any[];
  onToggleColumn: (columnName: string) => void;
}) {
  return (
    <Menu shadow="xs" closeOnItemClick={false}>
      <Menu.Target>
        <ActionIcon>
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
                onChange={(event) => onToggleColumn(col.accessor)}
                radius="sm"
              />
            </Menu.Item>
          ))}
      </Menu.Dropdown>
    </Menu>
  );
}
