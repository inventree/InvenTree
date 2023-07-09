import axios from 'axios';
import { DataTable, DataTableSortStatus } from "mantine-datatable";
import { Component } from "react";
import { useState } from 'react';
import { Text } from '@mantine/core';

import { useQuery } from '@tanstack/react-query';
import { api, queryClient } from '../../App';

/**
 * Table Component which extends DataTable with custom InvenTree functionality
 */

export function InvenTreeTable({
    url,
    params,
    columns,
    paginated=true,
    pageSize=25,
    tableKey=''
} : {
    url: string;
    params: any;
    columns: any;
    paginated: boolean;
    pageSize: number;
    tableKey: string;
}) {

    const [page, setPage] = useState(1);
    const [sortStatus, setSortStatus] = useState<DataTableSortStatus>({ columnAccessor: 'name', direction: 'asc' });

    const handleSortStatusChange = (status: DataTableSortStatus) => {
        setPage(1);
        setSortStatus(status);
    };

    // Function to perform API query to fetch required data
    function fetchTableData() {
        
        let queryParams = Object.assign({}, params);

        if (paginated) {
            queryParams.limit = PAGE_SIZE;
            queryParams.offset = (page - 1) * PAGE_SIZE;
        }
            
        return api
            .get(`http://localhost:8000/api/${url}`, {params: queryParams})
            .then(function(response) {
                if ('results' in response.data) {
                    // Handle paginated response
                    return response.data.results;
                } else {
                    // Handle non-paginated response
                    return response.data;
                }
            });
    }

    const { isLoading, error, data, isFetching } = useQuery({
        queryKey: [`table-${tableKey}`],
        queryFn: fetchTableData,
        refetchOnWindowFocus: false,
    });

    const PAGE_SIZE = 25;

    // TODO: Enable pagination
    // TODO: Handle data sorting

    return <DataTable
        withBorder
        fetching={isFetching}
        records={data || []}
        columns={columns}
    />;
}
