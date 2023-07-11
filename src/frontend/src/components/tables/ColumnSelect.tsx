import { Checkbox, Menu } from "@mantine/core";
import { t } from '@lingui/macro';
import { ActionIcon } from "@mantine/core";
import { IconAdjustments } from "@tabler/icons-react";
import { notYetImplemented } from "../../functions/notifications";

export function TableColumnSelect({
    columns
} : { 
    columns: any[];
}) {

    // TODO: When a column is hidden, it should be removed from the table
    function toggleColumn(columnName: string) {
        console.log("toggle column:", columnName);
        notYetImplemented();
    }

    return <Menu shadow="xs">
        <Menu.Target>
            <ActionIcon>
                <IconAdjustments />
            </ActionIcon>
        </Menu.Target>

        <Menu.Dropdown>
            <Menu.Label>{t`Select Columns`}</Menu.Label>
            {columns.filter((col) => col.switchable).map((col) => 
                <Menu.Item>
                    <Checkbox checked={!col.hidden} label={col.title} onChange={(event) => toggleColumn(col.accessor)}/>
                </Menu.Item>
            )}
        </Menu.Dropdown>
    </Menu>;
}
