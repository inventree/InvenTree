import { t } from '@lingui/macro';
import { Badge, Group, Paper, Stack, Text } from '@mantine/core';
import { Dropzone } from '@mantine/dropzone';
import { notifications } from '@mantine/notifications';
import {
  IconExternalLink,
  IconFileUpload,
  IconUpload,
  IconX
} from '@tabler/icons-react';
import { ReactNode, useCallback, useEffect, useMemo, useState } from 'react';

import { api } from '../../App';
import { ActionButton } from '../../components/buttons/ActionButton';
import { ApiFormFieldSet } from '../../components/forms/fields/ApiFormField';
import { AttachmentLink } from '../../components/items/AttachmentLink';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
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
      sortable: false,
      switchable: false,
      noWrap: true,
      render: function (record: any) {
        if (record.attachment) {
          return <AttachmentLink attachment={record.attachment} />;
        } else if (record.link) {
          return <AttachmentLink attachment={record.link} external />;
        } else {
          return '-';
        }
      }
    },
    {
      accessor: 'comment',
      sortable: false,

      render: function (record: any) {
        return record.comment;
      }
    },
    {
      accessor: 'upload_date',
      sortable: true,

      render: function (record: any) {
        return (
          <Group justify="space-between">
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
  model_type,
  model_id
}: {
  model_type: ModelType;
  model_id: number;
}): ReactNode {
  const table = useTable(`${model_type}-attachments`);

  const tableColumns = useMemo(() => attachmentTableColumns(), []);

  const [allowEdit, setAllowEdit] = useState<boolean>(false);
  const [allowDelete, setAllowDelete] = useState<boolean>(false);

  const url = apiUrl(ApiEndpoints.attachment_list);

  const validPk = useMemo(() => model_id > 0, [model_id]);

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
  }, [url]);

  const [isUploading, setIsUploading] = useState<boolean>(false);

  // Callback to upload file attachment(s)
  function uploadFiles(files: File[]) {
    files.forEach((file) => {
      let formData = new FormData();
      formData.append('attachment', file);
      formData.append('model_type', model_type);
      formData.append('model_id', model_id.toString());

      setIsUploading(true);

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
        })
        .finally(() => {
          setIsUploading(false);
        });
    });
  }

  const [attachmentType, setAttachmentType] = useState<'attachment' | 'link'>(
    'attachment'
  );

  const [selectedAttachment, setSelectedAttachment] = useState<
    number | undefined
  >(undefined);

  const uploadFields: ApiFormFieldSet = useMemo(() => {
    let fields: ApiFormFieldSet = {
      model_type: {
        value: model_type,
        hidden: true
      },
      model_id: {
        value: model_id,
        hidden: true
      },
      attachment: {},
      link: {},
      comment: {}
    };

    if (attachmentType != 'link') {
      delete fields['link'];
    }

    // Remove the 'attachment' field if we are editing an existing attachment, or uploading a link
    if (attachmentType != 'attachment' || !!selectedAttachment) {
      delete fields['attachment'];
    }

    return fields;
  }, [model_type, model_id, attachmentType, selectedAttachment]);

  const uploadAttachment = useCreateApiFormModal({
    url: url,
    title: t`Upload Attachment`,
    fields: uploadFields,
    onFormSuccess: () => {
      table.refreshTable();
    }
  });

  const editAttachment = useEditApiFormModal({
    url: url,
    pk: selectedAttachment,
    title: t`Edit Attachment`,
    fields: uploadFields,
    onFormSuccess: (record: any) => {
      if (record.pk) {
        table.updateRecord(record);
      } else {
        table.refreshTable();
      }
    }
  });

  const deleteAttachment = useDeleteApiFormModal({
    url: url,
    pk: selectedAttachment,
    title: t`Delete Attachment`,
    onFormSuccess: () => {
      table.refreshTable();
    }
  });

  const tableActions: ReactNode[] = useMemo(() => {
    return [
      <ActionButton
        key="add-attachment"
        tooltip={t`Add attachment`}
        hidden={!allowEdit}
        icon={<IconFileUpload />}
        onClick={() => {
          setAttachmentType('attachment');
          setSelectedAttachment(undefined);
          uploadAttachment.open();
        }}
      />,
      <ActionButton
        key="add-external-link"
        tooltip={t`Add external link`}
        hidden={!allowEdit}
        icon={<IconExternalLink />}
        onClick={() => {
          setAttachmentType('link');
          setSelectedAttachment(undefined);
          uploadAttachment.open();
        }}
      />
    ];
  }, [allowEdit]);

  // Construct row actions for the attachment table
  const rowActions = useCallback(
    (record: any) => {
      let actions: RowAction[] = [];

      if (allowEdit) {
        actions.push(
          RowEditAction({
            onClick: () => {
              setSelectedAttachment(record.pk);
              editAttachment.open();
            }
          })
        );
      }

      if (allowDelete) {
        actions.push(
          RowDeleteAction({
            onClick: () => {
              setSelectedAttachment(record.pk);
              deleteAttachment.open();
            }
          })
        );
      }

      return actions;
    },
    [allowEdit, allowDelete]
  );

  return (
    <>
      {uploadAttachment.modal}
      {editAttachment.modal}
      {deleteAttachment.modal}
      <Stack gap="xs">
        {validPk && (
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
                model_type: model_type,
                model_id: model_id
              }
            }}
          />
        )}
        {allowEdit && validPk && (
          <Paper p="md" shadow="xs" radius="md">
            <Dropzone
              onDrop={uploadFiles}
              loading={isUploading}
              key="attachment-dropzone"
            >
              <Group justify="center" gap="lg" mih={100}>
                <Dropzone.Accept>
                  <IconUpload
                    style={{ color: 'var(--mantine-color-blue-6)' }}
                    stroke={1.5}
                  />
                </Dropzone.Accept>
                <Dropzone.Reject>
                  <IconX
                    style={{ color: 'var(--mantine-color-red-6)' }}
                    stroke={1.5}
                  />
                </Dropzone.Reject>
                <Dropzone.Idle>
                  <IconUpload
                    style={{ color: 'var(--mantine-color-dimmed)' }}
                    stroke={1.5}
                  />
                </Dropzone.Idle>
                <Text size="sm">{t`Drag attachment file here to upload`}</Text>
              </Group>
            </Dropzone>
          </Paper>
        )}
      </Stack>
    </>
  );
}
