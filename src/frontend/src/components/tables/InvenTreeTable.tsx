import { t } from '@lingui/macro';
import { DataTable, DataTableSortStatus } from "mantine-datatable";
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../App';

import { Space, Stack, Table, Text } from '@mantine/core';
import { Group } from '@mantine/core';

import { TableSearchInput } from './Search';

/**
 * Table Component which extends DataTable with custom InvenTree functionality
 */

export function InvenTreeTable({
    url,
    params,
    columns,
    allowSelection=false,
    allowSearch=true,
    paginated=true,
    pageSize=25,
    tableKey='',
    defaultSortColumn='',
    noRecordsText=t`No records found`,
} : {
    url: string;
    params: any;
    columns: any;
    tableKey: string;
    defaultSortColumn?: string;
    noRecordsText?: string;
    allowSelection?: boolean;
    allowSearch?: boolean;
    paginated?: boolean;
    pageSize?: number;
}) {

    // Pagination
    const [page, setPage] = useState(1);

    // Search term
    const [searchTerm, setSearchTerm] = useState<string>('');

    // Data Sorting
    const [sortStatus, setSortStatus] = useState<DataTableSortStatus>({ columnAccessor: defaultSortColumn, direction: 'asc' });

    // Missing records text (based on server response)
    const [missingRecordsText, setMissingRecordsText] = useState<string>(noRecordsText);

    // Data selection
    const [selectedRecords, setSelectedRecords] = useState<any[]>([]);

    const handleSortStatusChange = (status: DataTableSortStatus) => {
        setPage(1);
        setSortStatus(status);
    };

    // Function to perform API query to fetch required data
    const fetchTableData = async() => {
        
        let queryParams = Object.assign({}, params);

        // Handle pagination
        if (paginated) {
            queryParams.limit = pageSize;
            queryParams.offset = (page - 1) * pageSize;
        }

        // Handle custom search term
        if (searchTerm) {
            queryParams.search = searchTerm;
        }

        // Handle sorting
        if (sortStatus.columnAccessor) {
            if (sortStatus.direction == 'asc') {
                queryParams.ordering = sortStatus.columnAccessor;
            } else {
                queryParams.ordering = `-${sortStatus.columnAccessor}`;
            }
        }
            
        return api
            .get(`http://localhost:8000/api/${url}`, {  // TODO: Don't hardcode the base URL here!
                params: queryParams,
                timeout: 30 * 1000,
            }).then(function(response) {
                switch (response.status) {
                    case 200:
                        setMissingRecordsText(noRecordsText);
                        return response.data;
                    case 400:
                        setMissingRecordsText(t`Bad request`);
                        break;
                    case 401:
                        setMissingRecordsText(t`Unauthorized`);
                        break;
                    case 403:
                        setMissingRecordsText(t`Forbidden`);
                        break;
                    case 404:
                        setMissingRecordsText(t`Not found`);
                        break;
                    default:
                        setMissingRecordsText(t`Unknown error` + ": " + response.statusText); // TODO: Translate
                        break;
                }

                return [];
            }).catch(function(error) {
                setMissingRecordsText(t`Error` + ": " + error.message);
                return [];
            });
    }

    const { data, isFetching } = useQuery(
        [`table-${tableKey}`, sortStatus.columnAccessor, sortStatus.direction, page],
        async() => fetchTableData(),
        { refetchOnWindowFocus: false }
    );

    // TODO: Handle column hiding
    columns.forEach(function(col: any, idx: number) {
    });

    return <Stack>
        <Group position="apart">
            <Text>actions</Text>
            <Space />
            {allowSearch && <TableSearchInput />}
        </Group>
        <DataTable
            withBorder
            striped
            highlightOnHover
            idAccessor={'pk'}
            minHeight={100}
            totalRecords={data?.count ?? data?.length ?? 0}
            recordsPerPage={pageSize}
            page={page}
            onPageChange={setPage}
            sortStatus={sortStatus}
            onSortStatusChange={handleSortStatusChange}
            selectedRecords={allowSelection ? selectedRecords : undefined}
            onSelectedRecordsChange={allowSelection ? setSelectedRecords : undefined}
            fetching={isFetching}
            noRecordsText={missingRecordsText}
            records={data?.results ?? data ?? []}
            columns={columns}
        />
    </Stack>;
}
