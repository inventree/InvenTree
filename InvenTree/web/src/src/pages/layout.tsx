import { Outlet } from "react-router-dom";
import { HeaderTabs } from "../components/HeaderTabs";
import { Container, Flex, Space, Text } from "@mantine/core";

import { FooterSimple, FooterSimpleProps } from "../components/FooterSimple";
import { useStyles } from "../globalStyle";


export default function Layout({ user, tabs, links }: { user: any, tabs: any, links: FooterSimpleProps }) {
    const { classes } = useStyles();

    return (
        <Flex direction="column" mih="100vh">
        <HeaderTabs tabs={tabs} user={user} />
        <Container className={classes.content}><Outlet /></Container>
        <Space h="xl" />
        <FooterSimple links={links.links} />
        </Flex>
    );
}

export function Home() {

    return (<>
        <Text>Home</Text>
    </>);
}


export function Part() {

    return (<>
        <Text>Part</Text>
    </>);
}
