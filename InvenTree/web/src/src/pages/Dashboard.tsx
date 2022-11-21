import { Group } from "@mantine/core";
import { SimpleGrid, Chip } from "@mantine/core";
import { DashboardItem } from "./DashboardItem";
import { StylishText } from "../components/StylishText";
import { useSessionSettings } from "../states";


export function Dashboard() {
    const autoupdate = useSessionSettings((state) => state.autoupdate)
    const toffleAutoupdate = useSessionSettings((state) => state.toffleAutoupdate)

    const items = [
        { id: "starred-parts", text: "Subscribed Parts", icon: "fa-bell", url: "part", params: { starred: true } },
        { id: "starred-categories", text: "Subscribed Categories", icon: "fa-bell", url: "part/category", params: { starred: true } },
        { id: "latest-parts", text: "Latest Parts", icon: "fa-newspaper", url: "part", params: { ordering: "-creation_date", limit: 10 } },
        { id: "bom-validation", text: "BOM Waiting Validation", icon: "fa-times-circle", url: "part", params: { bom_valid: false } },
        { id: "recently-updated-stock", text: "Recently Updated", icon: "fa-clock", url: "stock", params: { part_detail: true, ordering: "-updated", limit: 10 } },
        { id: "low-stock", text: "Low Stock", icon: "fa-flag", url: "part", params: { low_stock: true } },
        { id: "depleted-stock", text: "Depleted Stock", icon: "fa-times", url: "part", params: { depleted_stock: true } },
        { id: "stock-to-build", text: "Required for Build Orders", icon: "fa-bullhorn", url: "part", params: { stock_to_build: true } },
        { id: "expired-stock", text: "Expired Stock", icon: "fa-calendar-times", url: "stock", params: { expired: true } },
        { id: "stale-stock", text: "Stale Stock", icon: "fa-stopwatch", url: "stock", params: { stale: true, expired: true } },
        { id: "build-pending", text: "Build Orders In Progress", icon: "fa-cogs", url: "build", params: { active: true } },
        { id: "build-overdue", text: "Overdue Build Orders", icon: "fa-calendar-times", url: "build", params: { overdue: true } },
        { id: "po-outstanding", text: "Outstanding Purchase Orders", icon: "fa-sign-in-alt", url: "order/po", params: { supplier_detail: true, outstanding: true } },
        { id: "po-overdue", text: "Overdue Purchase Orders", icon: "fa-calendar-times", url: "order/po", params: { supplier_detail: true, overdue: true } },
        { id: "so-outstanding", text: "Outstanding Sales Orders", icon: "fa-sign-out-alt", url: "order/so", params: { customer_detail: true, outstanding: true } },
        { id: "so-overdue", text: "Overdue Sales Orders", icon: "fa-calendar-times", url: "order/so", params: { customer_detail: true, overdue: true } },
        { id: "news", text: "Current News", icon: "fa-newspaper", url: "news", params: {} }
    ]

    return (<>
        <Group>
            <StylishText>Dashboard</StylishText>
            <Chip checked={autoupdate} onChange={() => toffleAutoupdate()}>Autoupdate</Chip>
        </Group>
        <SimpleGrid cols={4} pt="md" >{items.map((item) => <DashboardItem key={item.id} {...item} autoupdate={autoupdate} />)}</SimpleGrid>
    </>);
}
