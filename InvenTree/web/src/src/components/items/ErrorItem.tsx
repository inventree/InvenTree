import { Paper, Text } from '@mantine/core';
import { InvenTreeStyle } from '../../globalStyle';

export function ErrorItem({ id, error }: { id: string, error?: Error | null | undefined }) {
    const { classes } = InvenTreeStyle();
    const error_message = error?.message || error?.toString() || 'Unknown error';
    return (
        <Paper withBorder p="xs" radius="md" key={id} pos="relative" className={classes.error}>
            <Text>An error occured:</Text>
            {error_message}
        </Paper>
    );
}
