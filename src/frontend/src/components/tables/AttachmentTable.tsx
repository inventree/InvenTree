import { t } from '@lingui/macro';
import { Group, Stack, Text } from '@mantine/core';
import { Dropzone } from '@mantine/dropzone';
import { useId } from '@mantine/hooks';
import { randomId } from '@mantine/hooks';
import { notifications } from '@mantine/notifications';
import { IconFileUpload } from '@tabler/icons-react';
import { ReactNode, useEffect, useMemo, useState } from 'react';

import { api } from '../../App';
import { editAttachment } from '../../functions/forms/AttachmentForms';
import { notYetImplemented } from '../../functions/notifications';
import { AttachmentLink } from '../items/AttachmentLink';
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
      sortable: false,
      switchable: false,
      render: function (record: any) {
        if (record.attachment) {
          return <AttachmentLink attachment={record.attachment} />;
        } else if (record.link) {
          // TODO: Custom renderer for links
          return record.link;
        } else {
          return '-';
        }
      }
    },
    {
      accessor: 'comment',
      title: t`Comment`,
      sortable: false,
      switchable: true,
      render: function (record: any) {
        return record.comment;
      }
    },
    {
      accessor: 'uploaded',
      title: t`Uploaded`,
      sortable: false,
      switchable: true,
      render: function (record: any) {
        // TODO: Custom date renderer
        return record.upload_date;
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

  const [refreshKey, setRefreshKey] = useState<string>(randomId());

  const tableColumns = useMemo(() => attachmentTableColumns(), []);

  const [allowEdit, setAllowEdit] = useState<boolean>(false);
  const [allowDelete, setAllowDelete] = useState<boolean>(false);

  // Determine which permissions are available for this URL
  useEffect(() => {
    api
      .options(url)
      .then((response) => {
        let actions: any = response.data?.actions ?? {};

        setAllowEdit('POST' in actions);
        setAllowDelete('DELETE' in actions);
        return response;
      })
      .catch((error) => {
        return error;
      });
  }, []);

  function rowActions(record: any): RowAction[] {
    let actions: RowAction[] = [];

    if (allowEdit) {
      actions.push({
        title: t`Edit`,
        onClick: () => {
          editAttachment({
            url: url,
            model: model,
            pk: record.pk,
            callback: () => {
              setRefreshKey(randomId());
            }
          });
        }
      });
    }

    if (allowDelete) {
      actions.push({
        title: t`Delete`,
        onClick: () => {
          notYetImplemented();
        }
      });
    }

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

          setRefreshKey(randomId());

          return response;
        })
        .catch((error) => {
          console.error('error uploading attachment:', file, '->', error);
          notifications.show({
            title: t`Upload Error`,
            message: t`File could not be uploaded`,
            color: 'red'
          });
          return error;
        });
    });
  }

  return (
    <Stack spacing="xs">
      <InvenTreeTable
        url={url}
        tableKey={tableId}
        refreshKey={refreshKey}
        params={{
          [model]: pk
        }}
        columns={tableColumns}
        rowActions={allowEdit && allowDelete ? rowActions : undefined}
      />
      {allowEdit && (
        <Dropzone onDrop={uploadFiles}>
          <Dropzone.Idle>
            <Group position="center">
              <IconFileUpload size={24} />
              <Text size="sm">{t`Upload attachment`}</Text>
            </Group>
          </Dropzone.Idle>
        </Dropzone>
      )}
    </Stack>
  );
}
