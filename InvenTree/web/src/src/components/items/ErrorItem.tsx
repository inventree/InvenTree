import { Paper, Text } from '@mantine/core';

export function ErrorItem({ id, error }: { id: string, error?: Error }) {
    const error_message = error?.message || error?.toString() || 'Unknown error';
    return (
        <Paper withBorder p="xs" radius="md" key={id} pos="relative">
            <Text>An error occured:</Text>
            {error_message}
        </Paper>
    );
}
