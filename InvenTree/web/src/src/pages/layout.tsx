import { Outlet } from "react-router-dom";
import { HeaderTabs } from "../components/HeaderTabs";
import { Text } from "@mantine/core";

import { FooterSimple, FooterSimpleProps } from "../components/FooterSimple";


export default function Layout({ user, tabs, links }: {user: any, tabs: any, links: FooterSimpleProps}) {

    return (<>
        <HeaderTabs tabs={tabs} user={user}/>
        <Outlet />
        <FooterSimple links={links} />
    </>);
}

export function Dashboard() {

    return (<>
        <Text>Dashboard</Text>
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
