import { useCallback, useMemo } from 'react';

import { api } from '../App';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { apiUrl } from '../states/ApiState';
import { useInstance } from './UseInstance';

/*
 * Custom hook for managing the state of a data import session
 */

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
  availableFields: any[];
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

  const columnMappings: any[] = useMemo(() => {
    return sessionData?.column_mappings ?? [];
  }, [sessionData]);

  // List of fields which have been mapped to columns
  const mappedFields: any[] = useMemo(() => {
    return (
      sessionData?.column_mappings?.filter((column: any) => !!column.field) ??
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
    columnMappings,
    mappedFields
  };
}
