import { Outlet } from "react-router-dom";
import { HeaderTabs } from "../components/HeaderTabs";
import { Container, Text } from "@mantine/core";

import { FooterSimple, FooterSimpleProps } from "../components/FooterSimple";


export default function Layout({ user, tabs, links }: { user: any, tabs: any, links: FooterSimpleProps }) {

    return (<>
        <HeaderTabs tabs={tabs} user={user} />
        <Container>
            <Outlet />
        </Container>
        <FooterSimple links={links.links} />
    </>);
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
