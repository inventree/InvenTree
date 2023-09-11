import { t } from '@lingui/macro';
import { useId } from '@mantine/hooks';
import { ReactNode, useMemo } from 'react';

import { editAttachment } from '../../functions/forms/AttachmentForms';
import { notYetImplemented } from '../../functions/notifications';
import { TableColumn } from './Column';
import { InvenTreeTable } from './InvenTreeTable';
import { RowAction } from './RowActions';

function attachmentTableColumns(): TableColumn[] {
  return [
    {
      accessor: 'attachment',
      title: t`Attachment`,
      sortable: true,
      switchable: false,
      render: function (record: any) {
        if (record.attachment) {
          // TODO: Custom renderer for attachments
          return record.attachment;
        } else if (record.link) {
          // TODO: Custom renderer for links
          return record.link;
        } else {
          return '-';
        }
      }
    },
    {
      accessor: 'uploaded',
      title: t`Uploaded`,
      sortable: true,
      switchable: true,
      render: function (record: any) {
        // TODO: Custom date renderer
        return record.upload_date;
      }
    },
    {
      accessor: 'comment',
      title: t`Comment`,
      sortable: true,
      switchable: true,
      render: function (record: any) {
        return record.comment;
      }
    }
  ];
}

/**
 * Construct a table for displaying uploaded attachments
 */
export function AttachmentTable({
  url,
  model,
  pk
}: {
  url: string;
  pk: number;
  model: string;
}): ReactNode {
  const tableId = useId();

  const tableColumns = useMemo(() => attachmentTableColumns(), []);

  function rowActions(record: any): RowAction[] {
    let actions: RowAction[] = [];

    // TODO: Select actions based on user permissions
    actions.push({
      title: t`Edit`,
      onClick: () => {
        editAttachment({
          url: url,
          model: model,
          pk: record.pk,
          callback: () => {
            // TODO: refresh the attachment table
          }
        });
      }
    });

    // TODO: Only if user has 'delete' permission for this URL
    actions.push({
      title: t`Delete`,
      onClick: () => {
        notYetImplemented();
      }
    });

    return actions;
  }

  return (
    <InvenTreeTable
      url={url}
      tableKey={tableId}
      params={{
        [model]: pk
      }}
      columns={tableColumns}
      rowActions={rowActions}
    />
  );
}
