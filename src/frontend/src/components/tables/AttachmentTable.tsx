import { t } from '@lingui/macro';
import { useId } from '@mantine/hooks';
import { ReactNode, useMemo } from 'react';

import { TableColumn } from './Column';
import { InvenTreeTable } from './InvenTreeTable';

function attachmentTableColumns(): TableColumn[] {
  return [
    {
      accessor: 'attachment',
      title: t`Attachment`,
      sortable: true,
      switchable: false
    },
    {
      accessor: 'uploaded',
      title: t`Uploaded`,
      sortable: true,
      switchable: true
    },
    {
      accessor: 'comment',
      title: t`Comment`,
      sortable: true,
      switchable: true
    }
  ];
}

/**
 * Construct a table for displaying uploaded attachments
 */
export function AttachmentTable({
  url,
  params
}: {
  url: string;
  params?: object;
}): ReactNode {
  const tableId = useId();

  const tableColumns = useMemo(() => attachmentTableColumns(), []);

  return (
    <InvenTreeTable
      url={url}
      tableKey={tableId}
      params={params}
      columns={tableColumns}
    />
  );
}
