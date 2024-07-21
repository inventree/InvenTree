import { useCallback, useMemo } from 'react';

import { ApiEndpoints } from '../enums/ApiEndpoints';
import { useInstance } from './UseInstance';

/*
 * Custom hook for managing the state of a data import session
 */

// TODO: Load these values from the server?
export enum ImportSessionStatus {
  INITIAL = 0,
  MAPPING = 10,
  IMPORTING = 20,
  PROCESSING = 30,
  COMPLETE = 40
}

export type ImportSessionState = {
  sessionId: number;
  sessionData: any;
  setSessionData: (data: any) => void;
  refreshSession: () => void;
  sessionQuery: any;
  status: ImportSessionStatus;
  availableFields: Record<string, any>;
  availableColumns: string[];
  mappedFields: any[];
  columnMappings: any[];
  fieldDefaults: any;
  fieldOverrides: any;
  fieldFilters: any;
  rowCount: number;
  completedRowCount: number;
};

export function useImportSession({
  sessionId
}: {
  sessionId: number;
}): ImportSessionState {
  // Query manager for the import session
  const {
    instance: sessionData,
    setInstance,
    refreshInstance: refreshSession,
    instanceQuery: sessionQuery
  } = useInstance({
    endpoint: ApiEndpoints.import_session_list,
    pk: sessionId,
    defaultValue: {}
  });

  const setSessionData = useCallback((data: any) => {
    console.log('setting session data:');
    console.log(data);
    setInstance(data);
  }, []);

  // Current step of the import process
  const status: ImportSessionStatus = useMemo(() => {
    return sessionData?.status ?? ImportSessionStatus.INITIAL;
  }, [sessionData]);

  // List of available writeable database field definitions
  const availableFields: any[] = useMemo(() => {
    return sessionData?.available_fields ?? [];
  }, [sessionData]);

  // List of available data file columns
  const availableColumns: string[] = useMemo(() => {
    let cols = sessionData?.columns ?? [];

    // Filter out any blank or duplicate columns
    cols = cols.filter((col: string) => !!col);
    cols = cols.filter(
      (col: string, index: number) => cols.indexOf(col) === index
    );

    return cols;
  }, [sessionData.columns]);

  const columnMappings: any[] = useMemo(() => {
    let mapping =
      sessionData?.column_mappings?.map((mapping: any) => ({
        ...mapping,
        ...(availableFields[mapping.field] ?? {})
      })) ?? [];

    mapping = mapping.sort((a: any, b: any) => {
      if (a?.required && !b?.required) return -1;
      if (!a?.required && b?.required) return 1;
      return 0;
    });

    return mapping;
  }, [sessionData, availableColumns]);

  // List of field which have been mapped to columns
  const mappedFields: any[] = useMemo(() => {
    return (
      sessionData?.column_mappings?.filter((column: any) => !!column.column) ??
      []
    );
  }, [sessionData]);

  const fieldDefaults: any = useMemo(() => {
    return sessionData?.field_defaults ?? {};
  }, [sessionData]);

  const fieldOverrides: any = useMemo(() => {
    return sessionData?.field_overrides ?? {};
  }, [sessionData]);

  const fieldFilters: any = useMemo(() => {
    return sessionData?.field_filters ?? {};
  }, [sessionData]);

  const rowCount: number = useMemo(() => {
    return sessionData?.row_count ?? 0;
  }, [sessionData]);

  const completedRowCount: number = useMemo(() => {
    return sessionData?.completed_row_count ?? 0;
  }, [sessionData]);

  return {
    sessionData,
    setSessionData,
    sessionId,
    refreshSession,
    sessionQuery,
    status,
    availableFields,
    availableColumns,
    columnMappings,
    mappedFields,
    fieldDefaults,
    fieldOverrides,
    fieldFilters,
    rowCount,
    completedRowCount
  };
}
