import { useCallback, useMemo } from 'react';

import { api } from '../App';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { apiUrl } from '../states/ApiState';
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
  cancelSession: () => void;
  refreshSession: () => void;
  sessionQuery: any;
  status: ImportSessionStatus;
  availableFields: Record<string, any>;
  availableColumns: string[];
  mappedFields: any[];
  columnMappings: any[];
};

export function useImportSession({
  sessionId
}: {
  sessionId: number;
}): ImportSessionState {
  // Query manager for the import session
  const {
    instance: sessionData,
    refreshInstance: refreshSession,
    instanceQuery: sessionQuery
  } = useInstance({
    endpoint: ApiEndpoints.import_session_list,
    pk: sessionId,
    defaultValue: {}
  });

  // Cancel the importer session (by deleting it)
  const cancelSession = useCallback(() => {
    api.delete(apiUrl(ApiEndpoints.import_session_list, sessionId));
  }, [sessionId]);

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
  }, [sessionData]);

  const columnMappings: any[] = useMemo(() => {
    return sessionData?.column_mappings ?? [];
  }, [sessionData]);

  // List of field which have been mapped to columns
  const mappedFields: any[] = useMemo(() => {
    return (
      sessionData?.column_mappings?.filter((column: any) => !!column.column) ??
      []
    );
  }, [sessionData]);

  return {
    sessionData,
    sessionId,
    cancelSession,
    refreshSession,
    sessionQuery,
    status,
    availableFields,
    availableColumns,
    columnMappings,
    mappedFields
  };
}
