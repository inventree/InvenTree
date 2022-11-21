import { Outlet, useNavigate } from "react-router-dom";
import { HeaderTabs } from "../components/nav/HeaderTabs";
import { Center, Chip, Container, Flex, Space, Stack } from "@mantine/core";

import { FooterSimple, FooterSimpleProps } from "../components/nav/FooterSimple";
import { useStyles } from "../globalStyle";
import { StylishText } from "../components/StylishText";
import { ProtectedRoute, useAuth, UserProps } from "../contex/AuthContext";
import { AuthenticationForm } from "../components/AuthenticationForm";
import { hosts } from "../App";
import { useSessionSettings } from "../states";
import { useState } from "react";


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
    const hostOptions = hosts;
    const [ hostKey, setHostValue ] = useSessionSettings(state => [state.hostKey, state.setHost]);
    function changeHost(newVal: string) {
        console.log(newVal);
        setHostValue(hostOptions[newVal].host, newVal);
    }
    const hostname = (hostOptions[hostKey] === undefined) ? 'No selection' : hostOptions[hostKey].name;

    return (<Center mih='100vh'>
        <Stack>
            <Center>
                <Chip.Group position="center" m="md" multiple={false} value={hostKey} onChange={changeHost}>
                {Object.keys(hostOptions).map((key, index) => (<Chip key={key} value={key}>{hostOptions[key].name}</Chip>))}
                </Chip.Group>
            </Center>
            <Container w='md'><AuthenticationForm handleLogin={handleLogin} navigate={navigate} hostname={hostname} /></Container>
        </Stack>
    </Center>);
}

export function Logout() {
    const { handleLogout } = useAuth();
    const navigate = useNavigate();

    handleLogout();
    navigate('/');

    return (<></>);
}
