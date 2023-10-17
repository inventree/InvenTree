import { PartListTable } from './PartTable';

/**
 * Display variant parts for thespecified parent part
 */
export function PartVariantTable({ partId }: { partId: string }) {
  return (
    <PartListTable
      props={{
        enableDownload: false,
        customFilters: [],
        params: {
          ancestor: partId
        }
      }}
    />
  );
}
