import { DataTable, DataTableSortStatus } from "mantine-datatable";
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../App';

/**
 * Table Component which extends DataTable with custom InvenTree functionality
 */

export function InvenTreeTable({
    url,
    params,
    columns,
    allowSelection=false,
    paginated=true,
    pageSize=25,
    tableKey=''
} : {
    url: string;
    params: any;
    columns: any;
    tableKey: string;
    allowSelection?: boolean;
    paginated?: boolean;
    pageSize?: number;
}) {

    // Pagination
    const [page, setPage] = useState(1);

    // Data Sorting
    const [sortStatus, setSortStatus] = useState<DataTableSortStatus>({ columnAccessor: '', direction: 'asc' });

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

        // Handle sorting
        if (sortStatus.columnAccessor) {
            if (sortStatus.direction == 'asc') {
                queryParams.ordering = sortStatus.columnAccessor;
            } else {
                queryParams.ordering = `-${sortStatus.columnAccessor}`;
            }
        }
            
        return api
            .get(`http://localhost:8000/api/${url}`, {params: queryParams})
            .then((response) => response.data);
    }

    const { data, isFetching } = useQuery(
        [`table-${tableKey}`, sortStatus.columnAccessor, sortStatus.direction, page],
        async() => fetchTableData(),
        { refetchOnWindowFocus: false }
    );

    return <DataTable
        withBorder
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
        records={data?.results ?? data ?? []}
        columns={columns}
    />;
}
