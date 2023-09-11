import { t } from '@lingui/macro';
import { Group, Stack, Text } from '@mantine/core';
import { Dropzone } from '@mantine/dropzone';
import { useId } from '@mantine/hooks';
import { notifications } from '@mantine/notifications';
import { IconFileUpload } from '@tabler/icons-react';
import { ReactNode, useMemo } from 'react';

import { api } from '../../App';
import { editAttachment } from '../../functions/forms/AttachmentForms';
import { notYetImplemented } from '../../functions/notifications';
import { TableColumn } from './Column';
import { InvenTreeTable } from './InvenTreeTable';
import { RowAction } from './RowActions';

/**
 * Define set of columns to display for the attachment table
 */
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

  // Callback to upload file attachment(s)
  function uploadFiles(files: File[]) {
    files.forEach((file) => {
      let formData = new FormData();
      formData.append('attachment', file);
      formData.append(model, pk.toString());

      api
        .post(url, formData)
        .then((response) => {
          notifications.show({
            title: t`File uploaded`,
            message: t`File ${file.name} uploaded successfully`,
            color: 'green'
          });
          return response;
        })
        .catch((error) => {
          console.error('error uploading attachment:', file, '->', error);
          return error;
        });
    });
  }

  return (
    <Stack spacing="xs">
      <InvenTreeTable
        url={url}
        tableKey={tableId}
        params={{
          [model]: pk
        }}
        columns={tableColumns}
        rowActions={rowActions}
      />
      <Dropzone onDrop={uploadFiles}>
        <Dropzone.Accept>Accept?</Dropzone.Accept>
        <Dropzone.Reject>Reject?</Dropzone.Reject>
        <Dropzone.Idle>
          <Group position="center">
            <IconFileUpload size={24} />
            <Text size="sm">{t`Upload file`}</Text>
          </Group>
        </Dropzone.Idle>
      </Dropzone>
    </Stack>
  );
}
