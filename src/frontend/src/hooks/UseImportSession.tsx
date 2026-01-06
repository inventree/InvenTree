import { useCallback, useEffect, useMemo, useState } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import type { UseQueryResult } from '@tanstack/react-query';
import { useInstance } from './UseInstance';
import useStatusCodes from './UseStatusCodes';

/*
 * Custom hook for managing the state of a data import session
 */

export type ImportSessionState = {
  sessionId: number;
  sessionData: any;
  setSessionData: (data: any) => void;
  refreshSession: () => void;
  sessionQuery: UseQueryResult;
  status: number;
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
    hasPrimaryKey: true,
    defaultValue: {}
  });

  const setSessionData = useCallback((data: any) => {
    setInstance(data);
  }, []);

  useStatusCodes({
    modelType: ModelType.importsession
  });

  // Session status (we update whenever the session data changes)
  const [status, setStatus] = useState<number>(0);

  // Reset the status when the sessionId changes
  useEffect(() => {
    setStatus(0);
  }, [sessionId]);

  useEffect(() => {
    if (!!sessionData.status && sessionData.status !== status) {
      setStatus(sessionData.status);
    }
  }, [sessionData?.status]);

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
