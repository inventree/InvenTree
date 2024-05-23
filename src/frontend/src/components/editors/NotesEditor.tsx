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
  InsertThematicBreak,
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
  thematicBreakPlugin,
  toolbarPlugin
} from '@mdxeditor/editor';
import '@mdxeditor/editor/style.css';
import { IconUpload } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useEffect, useMemo } from 'react';
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
      tablePlugin(),
      thematicBreakPlugin()
    ];

    if (editable) {
      plg.push(
        toolbarPlugin({
          toolbarContents: () => (
            <>
              {' '}
              <ButtonWithTooltip
                title={t`Save Notes`}
                onClick={() => saveNotes()}
              >
                <IconUpload />
              </ButtonWithTooltip>
              <Separator />
              <UndoRedo />
              <Separator />
              <BoldItalicUnderlineToggles />
              <CodeToggle />
              <ListsToggle />
              <Separator />
              <BlockTypeSelect />
              <Separator />
              <CreateLink />
              <InsertImage />
              <InsertTable />
              <InsertAdmonition />
              <InsertThematicBreak />
            </>
          )
        })
      );
    }

    return plg;
  }, [editable]);

  return (
    <MDXEditor ref={ref} markdown={''} readOnly={!editable} plugins={plugins} />
  );
}
