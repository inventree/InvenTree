import { t } from "@lingui/macro";

import { InvenTreeTable } from "../InvenTreeTable";

import { TableColumn } from "../Column";

/**
 * Construct a list of columns for the build order table
 */
function buildOrderTableColumns(): TableColumn[] {
    return [
        {
            accessor: 'reference',
            sortable: true,
            title: t`Reference`,
            // TODO: Link to the build order detail page
        },
        {
            accessor: 'part',
            sortable: true,
            title: t`Part`,
        },
        {
            accessor: 'title',
            sortable: false,
            title: t`Description`,
            switchable: true,
        },
        {
            accessor: 'project_code',
            title: t`Project Code`,
            sortable: true,
            switchable: false,
            hidden: true,
            // TODO: Hide this if project code is not enabled
            // TODO: Custom render function here
        },
        {
            accessor: 'priority',
            title: t`Priority`,
            sortable: true,
            switchable: true,
        },
        {
            accessor: 'quantity',
            sortable: true,
            title: t`Quantity`,
            switchable: true,
        },
        {
            accessor: 'progress',
            sortable: true,
            title: t`Progress`,
            render: (record: any) => {
                return `${record.completed} / ${record.quantity}`;
            },
            ordering: 'quantity',
        },
        {
            accessor: 'status',
            sortable: true,
            title: t`Status`,
            switchable: true,
            // TODO: Custom render function here (status label)
        },
        {
            accessor: 'creation_date',
            sortable: true,
            title: t`Created`,
            switchable: true,
        },
        // TODO: issued_by
        // TODO: responsible
        // TODO: target_date
        // TODO: completion_date
    ];
}

/*
 * Construct a table of build orders, according to the provided parameters
 */
export function BuildOrderTable({
    params={}
} : {
    params?: any;
}) {

    // Add required query parameters
    let tableParams = Object.assign({}, params);

    tableParams.part_detail = true;

    return <InvenTreeTable
        url='build/'
        params={tableParams}
        enableDownload
        tableKey="build-order-table"
        columns={buildOrderTableColumns()}
        />;
}