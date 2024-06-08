import { t } from '@lingui/macro';
import { notifications } from '@mantine/notifications';
import {
  AdmonitionDirectiveDescriptor,
  BlockTypeSelect,
  BoldItalicUnderlineToggles,
  ButtonWithTooltip,
  CodeToggle,
  CreateLink,
  InsertAdmonition,
  InsertImage,
  InsertTable,
  ListsToggle,
  MDXEditor,
  type MDXEditorMethods,
  Separator,
  UndoRedo,
  directivesPlugin,
  headingsPlugin,
  imagePlugin,
  linkDialogPlugin,
  linkPlugin,
  listsPlugin,
  markdownShortcutPlugin,
  quotePlugin,
  tablePlugin,
  toolbarPlugin
} from '@mdxeditor/editor';
import '@mdxeditor/editor/style.css';
import { IconDeviceFloppy, IconEdit, IconEye } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { ReactNode, useCallback, useEffect, useMemo, useState } from 'react';
import React from 'react';

import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { apiUrl } from '../../states/ApiState';
import { useLocalState } from '../../states/LocalState';
import { ModelInformationDict } from '../render/ModelType';

/*
 * Upload an drag-n-dropped image to the server against a model type and instance.
 */
async function uploadNotesImage(
  image: File,
  modelType: ModelType,
  modelId: number
): Promise<string> {
  const formData = new FormData();
  formData.append('image', image);

  formData.append('model_type', modelType);
  formData.append('model_id', modelId.toString());

  const response = await api
    .post(apiUrl(ApiEndpoints.notes_image_upload), formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    .catch(() => {
      notifications.hide('notes');
      notifications.show({
        title: t`Error`,
        message: t`Image upload failed`,
        color: 'red',
        id: 'notes'
      });
    });

  return response?.data?.image ?? '';
}

/*
 * A text editor component for editing notes against a model type and instance.
 * Uses the MDXEditor component - https://mdxeditor.dev/
 *
 * TODO:
 * - Disable editing by default when the component is launched - user can click an "edit" button to enable
 * - Allow image resizing in the future (requires back-end validation changes))
 * - Allow user to configure the editor toolbar (i.e. hide some buttons if they don't want them)
 */
export default function NotesEditor({
  modelType,
  modelId,
  editable
}: {
  modelType: ModelType;
  modelId: number;
  editable?: boolean;
}) {
  const ref = React.useRef<MDXEditorMethods>(null);

  const { host } = useLocalState();

  // In addition to the editable prop, we also need to check if the user has "enabled" editing
  const [editing, setEditing] = useState<boolean>(false);

  useEffect(() => {
    // Initially disable editing mode on load
    setEditing(false);
  }, [editable, modelId, modelType]);

  const noteUrl: string = useMemo(() => {
    const modelInfo = ModelInformationDict[modelType];
    return apiUrl(modelInfo.api_endpoint, modelId);
  }, [modelType, modelId]);

  const imageUploadHandler = useCallback(
    (image: File): Promise<string> => {
      return uploadNotesImage(image, modelType, modelId);
    },
    [modelType, modelId]
  );

  const imagePreviewHandler = useCallback(
    async (image: string): Promise<string> => {
      // If the image is a relative URL, then we need to prepend the base URL
      if (image.startsWith('/media/')) {
        image = host + image;
      }

      return image;
    },
    [host]
  );

  const dataQuery = useQuery({
    queryKey: [noteUrl],
    queryFn: () =>
      api
        .get(noteUrl)
        .then((response) => response.data?.notes ?? '')
        .catch(() => ''),
    enabled: true
  });

  useEffect(() => {
    ref.current?.setMarkdown(dataQuery.data ?? '');
  }, [dataQuery.data, ref.current]);

  // Callback to save notes to the server
  const saveNotes = useCallback(() => {
    const markdown = ref.current?.getMarkdown() ?? '';
    api
      .patch(noteUrl, { notes: markdown })
      .then(() => {
        notifications.hide('notes');
        notifications.show({
          title: t`Success`,
          message: t`Notes saved successfully`,
          color: 'green',
          id: 'notes'
        });
      })
      .catch(() => {
        notifications.hide('notes');
        notifications.show({
          title: t`Error`,
          message: t`Failed to save notes`,
          color: 'red',
          id: 'notes'
        });
      });
  }, [noteUrl, ref.current]);

  const plugins: any[] = useMemo(() => {
    let plg = [
      directivesPlugin({
        directiveDescriptors: [AdmonitionDirectiveDescriptor]
      }),
      headingsPlugin(),
      imagePlugin({
        imageUploadHandler: imageUploadHandler,
        imagePreviewHandler: imagePreviewHandler,
        disableImageResize: true // Note: To enable image resize, we must allow HTML tags in the server
      }),
      linkPlugin(),
      linkDialogPlugin(),
      listsPlugin(),
      markdownShortcutPlugin(),
      quotePlugin(),
      tablePlugin()
    ];

    let toolbar: ReactNode[] = [];
    if (editable) {
      toolbar = [
        <ButtonWithTooltip
          key="toggle-editing"
          aria-label="toggle-notes-editing"
          title={editing ? t`Preview Notes` : t`Edit Notes`}
          onClick={() => setEditing(!editing)}
        >
          {editing ? <IconEye /> : <IconEdit />}
        </ButtonWithTooltip>
      ];

      if (editing) {
        toolbar = [
          ...toolbar,
          <ButtonWithTooltip
            key="save-notes"
            aria-label="save-notes"
            onClick={() => saveNotes()}
            title={t`Save Notes`}
            disabled={false}
          >
            <IconDeviceFloppy />
          </ButtonWithTooltip>,
          <Separator key="separator-1" />,
          <UndoRedo key="undo-redo" />,
          <Separator key="separator-2" />,
          <BoldItalicUnderlineToggles key="bold-italic-underline" />,
          <CodeToggle key="code-toggle" />,
          <ListsToggle key="lists-toggle" />,
          <Separator key="separator-3" />,
          <BlockTypeSelect key="block-type" />,
          <Separator key="separator-4" />,
          <CreateLink key="create-link" />,
          <InsertTable key="insert-table" />,
          <InsertAdmonition key="insert-admonition" />
        ];
      }
    }

    // If the user is allowed to edit, then add the toolbar
    if (editable) {
      plg.push(
        toolbarPlugin({
          toolbarContents: () => (
            <>
              {toolbar.map((item, index) => item)}
              {editing && <InsertImage />}
            </>
          )
        })
      );
    }

    return plg;
  }, [
    dataQuery.data,
    editable,
    editing,
    imageUploadHandler,
    imagePreviewHandler,
    saveNotes
  ]);

  return (
    <MDXEditor ref={ref} markdown={''} readOnly={!editable} plugins={plugins} />
  );
}
