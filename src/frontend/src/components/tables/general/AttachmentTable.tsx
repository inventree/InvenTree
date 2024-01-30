import { t } from '@lingui/macro';
import { Badge, Group, Stack, Text, Tooltip } from '@mantine/core';
import { ActionIcon } from '@mantine/core';
import { Dropzone } from '@mantine/dropzone';
import { notifications } from '@mantine/notifications';
import { IconExternalLink, IconFileUpload } from '@tabler/icons-react';
import { ReactNode, useEffect, useMemo, useState } from 'react';

import { api } from '../../../App';
import { ApiEndpoints } from '../../../enums/ApiEndpoints';
import {
  addAttachment,
  deleteAttachment,
  editAttachment
} from '../../../forms/AttachmentForms';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { AttachmentLink } from '../../items/AttachmentLink';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowAction, RowDeleteAction, RowEditAction } from '../RowActions';

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
      noWrap: true,
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

      render: function (record: any) {
        return record.comment;
      }
    },
    {
      accessor: 'uploaded',
      title: t`Uploaded`,
      sortable: false,

      render: function (record: any) {
        return (
          <Group position="apart">
            <Text>{record.upload_date}</Text>
            {record.user_detail && (
              <Badge size="xs">{record.user_detail.username}</Badge>
            )}
          </Group>
        );
      }
    }
  ];
}

/**
 * Construct a table for displaying uploaded attachments
 */
export function AttachmentTable({
  endpoint,
  model,
  pk
}: {
  endpoint: ApiEndpoints;
  pk: number;
  model: string;
}): ReactNode {
  const table = useTable(`${model}-attachments`);

  const tableColumns = useMemo(() => attachmentTableColumns(), []);

  const [allowEdit, setAllowEdit] = useState<boolean>(false);
  const [allowDelete, setAllowDelete] = useState<boolean>(false);

  const url = useMemo(() => apiUrl(endpoint), [endpoint]);

  const validPk = useMemo(() => pk > 0, [pk]);

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

  // Construct row actions for the attachment table
  function rowActions(record: any): RowAction[] {
    let actions: RowAction[] = [];

    if (allowEdit) {
      actions.push(
        RowEditAction({
          onClick: () => {
            editAttachment({
              endpoint: endpoint,
              model: model,
              pk: record.pk,
              attachmentType: record.attachment ? 'file' : 'link',
              callback: table.refreshTable
            });
          }
        })
      );
    }

    if (allowDelete) {
      actions.push(
        RowDeleteAction({
          onClick: () => {
            deleteAttachment({
              endpoint: endpoint,
              pk: record.pk,
              callback: table.refreshTable
            });
          }
        })
      );
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

          table.refreshTable();

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

  const tableActions: ReactNode[] = useMemo(() => {
    let actions = [];

    if (allowEdit) {
      actions.push(
        <Tooltip label={t`Add attachment`} key="attachment-add">
          <ActionIcon
            radius="sm"
            onClick={() => {
              addAttachment({
                endpoint: endpoint,
                model: model,
                pk: pk,
                attachmentType: 'file',
                callback: table.refreshTable
              });
            }}
          >
            <IconFileUpload />
          </ActionIcon>
        </Tooltip>
      );

      actions.push(
        <Tooltip label={t`Add external link`} key="link-add">
          <ActionIcon
            radius="sm"
            onClick={() => {
              addAttachment({
                endpoint: endpoint,
                model: model,
                pk: pk,
                attachmentType: 'link',
                callback: table.refreshTable
              });
            }}
          >
            <IconExternalLink />
          </ActionIcon>
        </Tooltip>
      );
    }

    return actions;
  }, [allowEdit]);

  return (
    <Stack spacing="xs">
      {pk && pk > 0 && (
        <InvenTreeTable
          key="attachment-table"
          url={url}
          tableState={table}
          columns={tableColumns}
          props={{
            noRecordsText: t`No attachments found`,
            enableSelection: true,
            tableActions: tableActions,
            rowActions: allowEdit && allowDelete ? rowActions : undefined,
            params: {
              [model]: pk
            }
          }}
        />
      )}
      {allowEdit && validPk && (
        <Dropzone onDrop={uploadFiles} key="attachment-dropzone">
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
