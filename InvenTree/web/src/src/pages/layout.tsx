import { Outlet, useNavigate } from "react-router-dom";
import { HeaderTabs } from "../components/nav/HeaderTabs";
import { Center, Container, Flex, Space } from "@mantine/core";

import { FooterSimple, FooterSimpleProps } from "../components/nav/FooterSimple";
import { useStyles } from "../globalStyle";
import { StylishText } from "../components/StylishText";
import { ProtectedRoute, useAuth, UserProps } from "../contex/AuthContext";
import { AuthenticationForm } from "../components/AuthenticationForm";


export default function Layout({ user, tabs, links }: { user: UserProps, tabs: any, links: FooterSimpleProps }) {
    const { classes } = useStyles();

    return (
        <ProtectedRoute>
            <Flex direction="column" mih="100vh">
                <HeaderTabs tabs={tabs} user={user} />
                <Container className={classes.content}><Outlet /></Container>
                <Space h="xl" />
                <FooterSimple links={links.links} />
            </Flex>
        </ProtectedRoute>
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

export function Login() {
    const { handleLogin } = useAuth();
    const navigate = useNavigate();

    return (
        <Center mih='100vh'>
            <Container w='md'>
                <AuthenticationForm handleLogin={handleLogin} navigate={navigate} />
            </Container>
        </Center>
    );
}

export function Logout() {
    const { handleLogout } = useAuth();
    const navigate = useNavigate();

    handleLogout();
    navigate('/');

    return (<></>);
}
