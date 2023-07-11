import { Checkbox, Menu } from "@mantine/core";
import { Trans, t } from '@lingui/macro';
import { ActionIcon } from "@mantine/core";
import { IconAdjustments } from "@tabler/icons-react";

export function TableColumnSelect({
    columns
} : { 
    columns: any[];
}) {

    // TODO: When a column is hidden, it should be removed from the table

    return <Menu shadow="xs">
        <Menu.Target>
            <ActionIcon>
                <IconAdjustments />
            </ActionIcon>
        </Menu.Target>

        <Menu.Dropdown>
            <Menu.Label><Trans>Select Columns</Trans></Menu.Label>
            {columns.filter((col) => col.switchable).map((col) => 
                <Menu.Item>
                    <Checkbox checked={!col.hidden} label={col.title} onChange={(event) => col.hidden = !col.hidden}/>
                </Menu.Item>
            )}
        </Menu.Dropdown>
    </Menu>;
}
