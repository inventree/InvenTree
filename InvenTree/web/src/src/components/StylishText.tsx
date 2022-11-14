import { Text } from "@mantine/core";
import { useStyles } from "../globalStyle";

export function StylishText({children}: {childre: any }) {
    const { classes } = useStyles();
    return (
        <Text className={classes.signText} variant="gradient" gradient={{ from: 'indigo', to: 'cyan', deg: 45 }}>{children}</Text>
    );
}
