import { t } from '@lingui/core/macro';
import { notifications } from '@mantine/notifications';
import { useQuery } from '@tanstack/react-query';
import DOMPurify from 'dompurify';
import EasyMDE, { type default as SimpleMde } from 'easymde';
import 'easymde/dist/easymde.min.css';
import { useCallback, useEffect, useMemo, useState } from 'react';
import SimpleMDE from 'react-simplemde-editor';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelInformationDict } from '@lib/enums/ModelInformation';
import type { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import { useApi } from '../../contexts/ApiContext';

import '@blocknote/core/fonts/inter.css';
import { BlockNoteView } from '@blocknote/mantine';
import '@blocknote/mantine/style.css';
import { useCreateBlockNote } from '@blocknote/react';
import {
  Box,
  Button,
  Flex,
  Group,
  Paper,
  Stack,
  Tabs,
  Text
} from '@mantine/core';
import { IconCirclePlus } from '@tabler/icons-react';
import { useNoteFields } from '../../forms/CommonForms';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { useUserState } from '../../states/UserState';

export default function NotesEditor({
  modelType,
  modelId,
  editable,
  setDirtyCallback
}: Readonly<{
  modelType: ModelType;
  modelId: number;
  editable?: boolean;
  setDirtyCallback?: (dirty: boolean) => void;
}>) {
  const api = useApi();
  const user = useUserState();

  // The ID of the selected note
  const [selectedNote, setSelectedNote] = useState<number | undefined>(
    undefined
  );

  // Fetch the available notes for the given model type and ID
  const notesQuery = useQuery({
    queryKey: ['notes', modelType, modelId],
    queryFn: async () => {
      return api
        .get(apiUrl(ApiEndpoints.note_list), {
          params: {
            model_id: modelId,
            model_type: modelType
          }
        })
        .then((response) => response.data ?? []);
    },
    staleTime: 0,
    refetchOnWindowFocus: false,
    refetchOnMount: true,
    enabled: !!modelId && !!modelType
  });

  // Adjust the note selection
  useEffect(() => {
    // If the currently selected note is not in the list of available notes, then we need to adjust the selection
    if (
      selectedNote &&
      notesQuery.data &&
      !notesQuery.data.some((note: any) => note.pk === selectedNote)
    ) {
      setSelectedNote(
        notesQuery.data.length > 0 ? notesQuery.data[0].pk : undefined
      );
    }
  }, [notesQuery.data]);

  const canEdit = useMemo(
    () =>
      user.hasChangePermission(modelType) &&
      notesQuery.isFetched &&
      notesQuery.isSuccess,
    [user, modelType, notesQuery]
  );

  const editor = useCreateBlockNote();

  const noteFields = useNoteFields({ modelType: modelType, modelId: modelId });

  const createNote = useCreateApiFormModal({
    title: t`Add Note`,
    fields: noteFields,
    url: apiUrl(ApiEndpoints.note_list),
    method: 'POST',
    successMessage: null,
    onFormSuccess: (response: any) => {
      notesQuery.refetch().then(() => {
        // Select the newly created note
        setSelectedNote(response.pk);
      });
    }
  });

  return (
    <>
      {createNote.modal}
      <Flex align='left'>
        <Box style={{ flex: 1 }}>
          <Paper p='md' shadow='sm' withBorder>
            <BlockNoteView
              editor={editor}
              content={''}
              editable={canEdit}
              style={{ minHeight: '400px' }}
            />
          </Paper>
        </Box>
        <Stack gap='xs'>
          <Button leftSection={<IconCirclePlus />} onClick={createNote.open}>
            {t`Add Note`}
          </Button>
          <Tabs
            orientation='vertical'
            placement='right'
            value={selectedNote?.toString()}
          >
            <Tabs.List style={{ minWidth: '200px' }}>
              {notesQuery.data?.map((note: any) => (
                <Tabs.Tab
                  key={note.pk}
                  value={note.pk?.toString()}
                  onClick={() => setSelectedNote(note.pk)}
                >
                  <Group gap='xs' wrap='nowrap'>
                    <Text size='sm'>{note.title}</Text>
                  </Group>
                </Tabs.Tab>
              ))}
            </Tabs.List>
          </Tabs>
        </Stack>
      </Flex>
    </>
  );
}

/*
 * A text editor component for editing notes against a model type and instance.
 * Uses the react-simple-mde editor: https://github.com/RIP21/react-simplemde-editor
 *
 * TODO:
 * - Disable editing by default when the component is launched - user can click an "edit" button to enable
 * - Allow image resizing in the future (requires back-end validation changes))
 * - Allow user to configure the editor toolbar (i.e. hide some buttons if they don't want them)
 */
export function OldNotesEditor({
  modelType,
  modelId,
  editable,
  setDirtyCallback
}: Readonly<{
  modelType: ModelType;
  modelId: number;
  editable?: boolean;
  setDirtyCallback?: (dirty: boolean) => void;
}>) {
  const api = useApi();
  // In addition to the editable prop, we also need to check if the user has "enabled" editing
  const [editing, setEditing] = useState<boolean>(false);
  const [localIsDirty, setLocalIsDirty] = useState<boolean>(false);

  const [markdown, setMarkdown] = useState<string>('');

  useEffect(() => {
    // Initially disable editing mode on load
    setEditing(false);
  }, [editable, modelId, modelType]);

  useEffect(() => {
    setDirtyCallback?.(localIsDirty);
  }, [localIsDirty]);

  const noteUrl: string = useMemo(() => {
    const modelInfo = ModelInformationDict[modelType];
    return apiUrl(modelInfo.api_endpoint, modelId);
  }, [modelType, modelId]);

  // Image upload handler
  const imageUploadHandler = useCallback(
    (
      file: File,
      onSuccess: (url: string) => void,
      onError: (error: string) => void
    ) => {
      const formData = new FormData();
      formData.append('image', file);

      formData.append('model_type', modelType);
      formData.append('model_id', modelId.toString());

      api
        .post(apiUrl(ApiEndpoints.notes_image_upload), formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        .catch((error) => {
          onError(error.message);
          notifications.hide('notes');
          notifications.show({
            id: 'notes',
            title: t`Error`,
            message: t`Image upload failed`,
            color: 'red'
          });
        })
        .then((response: any) => {
          onSuccess(response.data.image);
          notifications.hide('notes');
          notifications.show({
            id: 'notes',
            title: t`Success`,
            message: t`Image uploaded successfully`,
            color: 'green'
          });
        });
    },
    [modelType, modelId]
  );

  const dataQuery = useQuery({
    queryKey: ['notes-editor', noteUrl, modelType, modelId],
    retry: 5,
    queryFn: () =>
      api.get(noteUrl).then((response) => response.data?.notes ?? ''),
    enabled: true
  });

  // Update internal markdown data when the query data changes
  useEffect(() => {
    setMarkdown(dataQuery.data ?? '');
  }, [dataQuery.data]);

  // Callback to save notes to the server
  const saveNotes = useCallback(
    (markdown: string) => {
      if (!noteUrl) {
        return;
      }

      api
        .patch(noteUrl, { notes: markdown })
        .then(() => {
          notifications.hide('notes');
          notifications.show({
            title: t`Success`,
            message: t`Notes saved successfully`,
            color: 'green',
            id: 'notes',
            autoClose: 2000
          });
          setLocalIsDirty(false);
        })
        .catch((error) => {
          notifications.hide('notes');

          const msg =
            error?.response?.data?.non_field_errors[0] ??
            t`Failed to save notes`;

          notifications.show({
            title: t`Error Saving Notes`,
            message: msg,
            color: 'red',
            id: 'notes'
          });
        });
    },
    [api, noteUrl]
  );

  const editorOptions: SimpleMde.Options = useMemo(() => {
    const icons: any[] = [];

    if (editing) {
      icons.push({
        name: 'save-notes',
        action: (editor: SimpleMde) => {
          saveNotes(editor.value());
        },
        className: 'fa fa-save',
        title: t`Save Notes`
      });

      icons.push('|');

      icons.push('heading-1', 'heading-2', 'heading-3', '|'); // Headings
      icons.push('bold', 'italic', 'strikethrough', '|'); // Text styles
      icons.push('unordered-list', 'ordered-list', 'code', 'quote', '|'); // Text formatting
      icons.push('table', 'link', 'image', '|');
      icons.push('horizontal-rule', '|', 'guide'); // Misc

      icons.push('|', 'undo', 'redo'); // Undo/Redo

      icons.push('|');

      icons.push({
        name: 'edit-disabled',
        action: () => setEditing(false),
        className: 'fa fa-times',
        title: t`Close Editor`
      });
    } else if (editable) {
      icons.push({
        name: 'edit-enabled',
        action: () => setEditing(true),
        className: 'fa fa-edit',
        title: t`Enable Editing`
      });
    }

    return {
      toolbar: icons,
      uploadImage: true,
      imagePathAbsolute: true,
      imageUploadFunction: imageUploadHandler,
      renderingConfig: {
        sanitizerFunction: (html: string) => {
          return DOMPurify.sanitize(html);
        }
      },
      sideBySideFullscreen: false,
      shortcuts: {},
      spellChecker: false
    };
  }, [editable, editing]);

  const [mdeInstance, setMdeInstance] = useState<SimpleMde | null>(null);

  useEffect(() => {
    if (mdeInstance) {
      const previewMode = !(editable && editing);

      mdeInstance.codemirror?.setOption('readOnly', previewMode);

      // Ensure the preview mode is toggled if required
      if (mdeInstance.isPreviewActive() != previewMode) {
        const sibling =
          mdeInstance?.codemirror.getWrapperElement()?.nextSibling;

        if (sibling != null && editable != false) {
          EasyMDE.togglePreview(mdeInstance);
        }
      }
    }
  }, [mdeInstance, editable, editing]);

  return (
    <SimpleMDE
      autoFocus
      getMdeInstance={(instance: SimpleMde) => setMdeInstance(instance)}
      onChange={(value: string) => {
        setMarkdown(value);
        setLocalIsDirty(true);
      }}
      options={editorOptions}
      value={markdown}
    />
  );
}
