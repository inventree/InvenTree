import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { InvenTreeTable } from '../InvenTreeTable';

export default function PartSalesAllocationsTable({
  partId
}: {
  partId: number;
}) {
  const table = useTable('partsalesallocations');

  return <></>;
}
