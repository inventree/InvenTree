import { Checkbox, Menu, Tooltip } from "@mantine/core";
import { t } from '@lingui/macro';
import { ActionIcon } from "@mantine/core";
import { IconAdjustments } from "@tabler/icons-react";
import { notYetImplemented } from "../../functions/notifications";

export function TableColumnSelect({
    columns,
    onToggleColumn,
} : { 
    columns: any[];
    onToggleColumn: (columnName: string) => void;
}) {

    return <Menu shadow="xs">
        <Menu.Target>
            <ActionIcon>
                <Tooltip label={t`Select Columns`}>
                    <IconAdjustments />
                </Tooltip>
            </ActionIcon>
        </Menu.Target>

        <Menu.Dropdown>
            <Menu.Label>{t`Select Columns`}</Menu.Label>
            {columns.filter((col) => col.switchable).map((col) => 
                <Menu.Item>
                    <Checkbox checked={!col.hidden} label={col.title || col.accessor} onChange={(event) => onToggleColumn(col.accessor)}/>
                </Menu.Item>
            )}
        </Menu.Dropdown>
    </Menu>;
}
