import { ActionIcon, Chip, CloseButton, Group, Indicator, Space, Text, Tooltip } from "@mantine/core";
import { IconMinus, IconPlus, IconTrash } from "@tabler/icons-react";
import { t } from "@lingui/macro";

/**
 * Return a table filter group component:
 * - Displays a list of active filters for the table
 * - Allows the user to add/remove filters
 * - Allows the user to clear all filters
 */
export function FilterGroup({
    filterList,
    onFilterAdd,
    onFilterRemove,
    onFilterClearAll
} : {
    filterList: any[];
    onFilterAdd: () => void;
    onFilterRemove: (filterName: string) => void;
    onFilterClearAll: () => void;
}) {

    return <Group position="right" spacing="xs">
        {filterList.map((filter) => 
            <Indicator
                color="red"
                label={<CloseButton title={t`Remove filter`} size="xs" onClick={() => onFilterRemove(filter.name)}/>}
                withBorder={false}
                size="xs"
            >
            <Chip checked={false}>
                <Text>{filter.label}</Text>
            </Chip>
            </Indicator>
        )}
        {true && 
            <ActionIcon variant="outline" onClick={() => onFilterClearAll()}>
                <Tooltip label={t`Clear all filters`}>
                    <IconTrash color="red" />
                </Tooltip>
            </ActionIcon>
        }
        <ActionIcon variant="outline" onClick={() => onFilterAdd()}>
            <Tooltip label={t`Add filter`}>
                <IconPlus color="green" />
            </Tooltip>
        </ActionIcon>
    </Group>;

}