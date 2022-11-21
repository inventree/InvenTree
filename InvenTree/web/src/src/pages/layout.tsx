import { Outlet } from "react-router-dom";
import { Header } from "../components/nav/Header";
import { Container, Flex, Space } from "@mantine/core";

import { Footer, FooterProps } from "../components/nav/Footer";
import { useStyles } from "../globalStyle";
import { ProtectedRoute } from "../contex/AuthContext";

export default function Layout({tabs, links }: {tabs: any, links: FooterProps }) {
    const { classes } = useStyles();

    return (
        <ProtectedRoute>
            <Flex direction="column" mih="100vh">
                <Header tabs={tabs}/>
                <Container className={classes.content}><Outlet /></Container>
                <Space h="xl" />
                <Footer links={links.links} />
            </Flex>
        </ProtectedRoute>
    );
}
