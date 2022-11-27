import { Paper, Text } from '@mantine/core';
import { InvenTreeStyle } from '../../globalStyle';
import { Trans } from '@lingui/macro'

export function ErrorItem({ id, error }: { id: string, error?: any }) {
    const { classes } = InvenTreeStyle();
    const error_message = error?.message || error?.toString() || <Trans>Unknown error</Trans>;
    return (
        <Paper withBorder p="xs" radius="md" key={id} pos="relative" className={classes.error}>
            <Text><Trans>An error occured:</Trans></Text>
            {error_message}
        </Paper>
    );
}
