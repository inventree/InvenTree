/**
 * Interface for the table filter, 
 */
export type TableFilter = {
    name: string;
    label: string;
    description?: string;
    type: string;
    options?: any[];
    defaultValue?: any;
    value?: any;
}
