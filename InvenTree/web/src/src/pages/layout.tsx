import { Outlet, useNavigate } from "react-router-dom";
import { HeaderTabs } from "../components/nav/HeaderTabs";
import { Center, Chip, Container, Flex, Space, Stack } from "@mantine/core";

import { FooterSimple, FooterSimpleProps } from "../components/nav/FooterSimple";
import { useStyles } from "../globalStyle";
import { StylishText } from "../components/StylishText";
import { ProtectedRoute, useAuth } from "../contex/AuthContext";
import { AuthenticationForm } from "../components/AuthenticationForm";
import { useSessionSettings } from "../states";

export default function Layout({tabs, links }: {tabs: any, links: FooterSimpleProps }) {
    const { classes } = useStyles();

    return (
        <ProtectedRoute>
            <Flex direction="column" mih="100vh">
                <HeaderTabs tabs={tabs}/>
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
    const [ hostKey, setHostValue, hostOptions, lastUsername ] = useSessionSettings(state => [state.hostKey, state.setHost, state.hostList, state.lastUsername]);
    function changeHost(newVal: string) {
        setHostValue(hostOptions[newVal].host, newVal);
    }
    const hostname = (hostOptions[hostKey] === undefined) ? 'No selection' : hostOptions[hostKey].name;

    function Login(username: string, password: string,) {
        handleLogin(username, password).then(() => {
            useSessionSettings.setState({ lastUsername: username });
            navigate('/');
        });
    }
    function Register(name: string, username: string, password: string) {
        // TODO: Register
        console.log('Registering is not implemented yet');
        console.log(name, username, password);
    }

    return (<Center mih='100vh'>
        <Stack>
            <Center>
                <Chip.Group position="center" m="md" multiple={false} value={hostKey} onChange={changeHost}>
                {Object.keys(hostOptions).map((key) => (<Chip key={key} value={key}>{hostOptions[key].name}</Chip>))}
                </Chip.Group>
            </Center>
            <Container w='md'><AuthenticationForm Login={Login} Register={Register} hostname={hostname} lastUsername={lastUsername} /></Container>
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
