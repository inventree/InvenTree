import { Outlet } from "react-router-dom";
import { HeaderTabs } from "../components/HeaderTabs";
import { Text } from "@mantine/core";

import { FooterSimple } from "../components/FooterSimple";


export default function Layout({ user, tabs, links }: any) {

    return (<>
        <HeaderTabs tabs={tabs} user={user}/>
        <Outlet />
        <FooterSimple links={links} />
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
