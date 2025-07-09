import { t } from '@lingui/core/macro';
import { Badge, Group, Paper, Stack, Text } from '@mantine/core';
import { Dropzone } from '@mantine/dropzone';
import { notifications } from '@mantine/notifications';
import {
  IconCircleCheck,
  IconExclamationCircle,
  IconExternalLink,
  IconFileUpload,
  IconUpload,
  IconX
} from '@tabler/icons-react';
import { type ReactNode, useCallback, useMemo, useState } from 'react';

import { ActionButton } from '@lib/components/ActionButton';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import type { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import type { TableFilter } from '@lib/types/Filters';
import type { ApiFormFieldSet } from '@lib/types/Forms';
import type { TableColumn } from '@lib/types/Tables';
import { AttachmentLink } from '../../components/items/AttachmentLink';
import { ProgressBar } from '../../components/items/ProgressBar';
import { useApi } from '../../contexts/ApiContext';
import { formatFileSize } from '../../defaults/formatters';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import { InvenTreeTable } from '../InvenTreeTable';
import { type RowAction, RowDeleteAction, RowEditAction } from '../RowActions';

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
      render: (record: any) => {
        if (record.attachment) {
          return <AttachmentLink attachment={record.attachment} />;
        } else if (record.link) {
          return <AttachmentLink attachment={record.link} external />;
        } else {
          return '-';
        }
      },
      noContext: true
    },
    {
      accessor: 'comment',
      sortable: false,

      render: (record: any) => {
        return record.comment;
      }
    },
    {
      accessor: 'upload_date',
      sortable: true,

      render: (record: any) => {
        return (
          <Group justify='space-between'>
            <Text>{record.upload_date}</Text>
            {record.user_detail && (
              <Badge size='xs'>{record.user_detail.username}</Badge>
            )}
          </Group>
        );
      }
    },
    {
      accessor: 'file_size',
      sortable: true,
      switchable: true,
      render: (record: any) => {
        if (!record.attachment) {
          return '-';
        } else {
          return formatFileSize(record.file_size);
        }
      }
    }
  ];
}

function UploadProgress({
  filename,
  progress
}: {
  filename: string;
  progress: number;
}) {
  return (
    <Stack gap='xs'>
      <Text size='sm'>{t`Uploading file ${filename}`}</Text>
      <ProgressBar value={progress} progressLabel={false} />
    </Stack>
  );
}

/**
 * Construct a table for displaying uploaded attachments
 */
export function AttachmentTable({
  model_type,
  model_id
}: Readonly<{
  model_type: ModelType;
  model_id: number;
}>): ReactNode {
  const api = useApi();
  const user = useUserState();
  const table = useTable(`${model_type}-attachments`);

  const tableColumns = useMemo(() => attachmentTableColumns(), []);

  const url = apiUrl(ApiEndpoints.attachment_list);

  const validPk = useMemo(() => model_id > 0, [model_id]);

  const canDelete = useMemo(
    () => user.hasDeletePermission(model_type),
    [user, model_type]
  );

  const [isUploading, setIsUploading] = useState<boolean>(false);

  const allowDragAndDrop: boolean = useMemo(() => {
    return user.hasAddPermission(model_type);
  }, [user, model_type]);

  // Callback to upload file attachment(s)
  function uploadFiles(files: File[]) {
    files.forEach((file) => {
      const formData = new FormData();
      formData.append('attachment', file);
      formData.append('model_type', model_type);
      formData.append('model_id', model_id.toString());

      setIsUploading(true);

      const name: string = file.name;
      const id: string = `attachment-upload-${model_type}-${model_id}-${file.name}`;

      notifications.show({
        id: id,
        title: t`Uploading File`,
        message: <UploadProgress filename={name} progress={0} />,
        color: 'blue',
        loading: true,
        autoClose: false
      });

      api
        .post(url, formData, {
          timeout: 30 * 1000,
          onUploadProgress: (progressEvent) => {
            const progress = 100 * (progressEvent?.progress ?? 0);
            notifications.update({
              id: id,
              title: t`Uploading File`,
              color: 'blue',
              loading: true,
              autoClose: false,
              message: <UploadProgress filename={name} progress={progress} />
            });
          }
        })
        .then((response) => {
          notifications.update({
            id: id,
            title: t`File Uploaded`,
            message: t`File ${name} uploaded successfully`,
            color: 'green',
            autoClose: 3500,
            icon: <IconCircleCheck />,
            loading: false
          });

          table.refreshTable();

          return response;
        })
        .catch((error) => {
          console.error('Error uploading attachment:', file, '->', error);
          notifications.update({
            id: id,
            title: t`Upload Error`,
            message: t`File could not be uploaded`,
            color: 'red',
            autoClose: 5000,
            icon: <IconExclamationCircle />,
            loading: false
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
    const fields: ApiFormFieldSet = {
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

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'is_link',
        label: t`Is Link`,
        description: t`Show link attachments`
      },
      {
        name: 'is_file',
        label: t`Is File`,
        description: t`Show file attachments`
      }
    ];
  }, []);

  const tableActions: ReactNode[] = useMemo(() => {
    return [
      <ActionButton
        key='add-attachment'
        tooltip={t`Add attachment`}
        hidden={!user.hasAddPermission(model_type)}
        icon={<IconFileUpload />}
        onClick={() => {
          setAttachmentType('attachment');
          setSelectedAttachment(undefined);
          uploadAttachment.open();
        }}
      />,
      <ActionButton
        key='add-external-link'
        tooltip={t`Add external link`}
        hidden={!user.hasAddPermission(model_type)}
        icon={<IconExternalLink />}
        onClick={() => {
          setAttachmentType('link');
          setSelectedAttachment(undefined);
          uploadAttachment.open();
        }}
      />
    ];
  }, [user, model_type]);

  // Construct row actions for the attachment table
  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        RowEditAction({
          hidden: !user.hasChangePermission(model_type),
          onClick: () => {
            setSelectedAttachment(record.pk);
            editAttachment.open();
          }
        }),
        RowDeleteAction({
          hidden: !canDelete,
          onClick: () => {
            setSelectedAttachment(record.pk);
            deleteAttachment.open();
          }
        })
      ];
    },
    [user, model_type]
  );

  return (
    <>
      {uploadAttachment.modal}
      {editAttachment.modal}
      {deleteAttachment.modal}
      <Stack gap='xs'>
        {validPk && (
          <InvenTreeTable
            key='attachment-table'
            url={url}
            tableState={table}
            columns={tableColumns}
            props={{
              noRecordsText: t`No attachments found`,
              enableSelection: canDelete,
              enableBulkDelete: canDelete,
              tableActions: tableActions,
              tableFilters: tableFilters,
              rowActions: rowActions,
              params: {
                model_type: model_type,
                model_id: model_id
              }
            }}
          />
        )}
        {allowDragAndDrop && validPk && (
          <Paper p='md' shadow='xs' radius='md'>
            <Dropzone
              onDrop={uploadFiles}
              loading={isUploading}
              key='attachment-dropzone'
            >
              <Group justify='center' gap='lg' mih={100}>
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
                <Text size='sm'>{t`Drag attachment file here to upload`}</Text>
              </Group>
            </Dropzone>
          </Paper>
        )}
      </Stack>
    </>
  );
}
