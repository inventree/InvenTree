import { Outlet } from "react-router-dom";
import { HeaderTabs } from "../components/HeaderTabs";
import { Container, Flex, Space } from "@mantine/core";

import { FooterSimple, FooterSimpleProps } from "../components/FooterSimple";
import { useStyles } from "../globalStyle";
import { StylishText } from "../components/StylishText";


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
        <StylishText>Home</StylishText>
    </>);
}


export function Part() {

    return (<>
        <StylishText>Part</StylishText>
    </>);
}
