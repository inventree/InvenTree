/**
 * Interface for the table column definition
 */
export type TableColumn = {
    accessor: string;
    title: string;
    sortable?: boolean;
    switchable?: boolean;
    hidden?: boolean;
    render?: (record: any) => any;
    filter?: any;
    filtering?: boolean;
    width?: number;
}
