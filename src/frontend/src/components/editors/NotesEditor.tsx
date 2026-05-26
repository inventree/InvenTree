import { t } from '@lingui/core/macro';
import { RichTextEditor } from '@mantine/tiptap';
import '@mantine/tiptap/styles.css';
import { useHotkeys } from '@mantine/hooks';
import { notifications } from '@mantine/notifications';
import { useQuery } from '@tanstack/react-query';
import { TableKit } from '@tiptap/extension-table';
import { useEditor, useEditorState } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import DOMPurify from 'dompurify';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ResizableImage } from 'tiptap-extension-resizable-image';
import 'tiptap-extension-resizable-image/styles.css';
import './NotesEditor.css';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import type { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import { useApi } from '../../contexts/ApiContext';

import { identifierString } from '@lib/functions/Conversion';
import {
  ActionIcon,
  Alert,
  Badge,
  Box,
  Button,
  FileButton,
  Flex,
  Group,
  HoverCard,
  Paper,
  Stack,
  Tabs,
  Text,
  Tooltip
} from '@mantine/core';
import {
  IconCirclePlus,
  IconColumnInsertLeft,
  IconColumnInsertRight,
  IconColumnRemove,
  IconDeviceFloppy,
  IconInfoCircle,
  IconPhoto,
  IconReload,
  IconRowInsertBottom,
  IconRowInsertTop,
  IconRowRemove,
  IconStar,
  IconTableOff,
  IconTablePlus,
  IconTableRow
} from '@tabler/icons-react';
import { useShallow } from 'zustand/react/shallow';
import { formatDate } from '../../defaults/formatters';
import { useNoteFields } from '../../forms/CommonForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useLocalState } from '../../states/LocalState';
import { useUserState } from '../../states/UserState';
import {
  DeleteItemAction,
  EditItemAction,
  OptionsActionDropdown
} from '../items/ActionDropdown';
import { RenderUser } from '../render/User';

function NoteInfoHover({ note }: { note: any }) {
  if (!note?.pk) {
    return null;
  }

  return (
    <HoverCard position='top-start'>
      <HoverCard.Target>
        <ActionIcon variant='transparent'>
          <IconInfoCircle />
        </ActionIcon>
      </HoverCard.Target>
      <HoverCard.Dropdown>
        <Paper p='sm' shadow='sm' withBorder>
          <Stack gap='xs'>
            {note.updated && (
              <Group gap='xs' justify='space-between'>
                <Text fw='bold'>{t`Updated`}</Text>
                <Text size='xs'>
                  {formatDate(note.updated, { showTime: true })}
                </Text>
              </Group>
            )}
            {note.updated_by_detail && (
              <Group gap='xs' justify='space-between'>
                <Text fw='bold'>{t`Updated by`}</Text>
                <RenderUser instance={note.updated_by_detail} />
              </Group>
            )}
          </Stack>
        </Paper>
      </HoverCard.Dropdown>
    </HoverCard>
  );
}

export default function NotesEditor({
  modelType,
  modelId,
  editable: _editable,
  setDirtyCallback: _setDirtyCallback
}: Readonly<{
  modelType: ModelType;
  modelId: number;
  editable?: boolean;
  setDirtyCallback?: (dirty: boolean) => void;
}>) {
  const api = useApi();
  const user = useUserState();
  const [_language] = useLocalState(useShallow((s) => [s.language]));
  const [searchParams, setSearchParams] = useSearchParams();

  const [isDirty, setIsDirty] = useState(false);

  const [selectedNoteId, setSelectedNoteId] = useState<number | undefined>(
    undefined
  );

  // Callback to upload an image file against the currently selected note
  const uploadFile = useCallback(
    async (file: File): Promise<string> => {
      const formData = new FormData();
      formData.append('note', selectedNoteId?.toString() ?? '');
      formData.append('image', file);

      return api
        .post(apiUrl(ApiEndpoints.notes_image_list), formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        .then((response) => response.data.image);
    },
    [selectedNoteId]
  );

  // Ref so editorProps handlers always call the latest uploadFile without stale closure
  const uploadFileRef = useRef(uploadFile);
  useEffect(() => {
    uploadFileRef.current = uploadFile;
  }, [uploadFile]);

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        link: { openOnClick: false }
      }),
      ResizableImage.configure({
        // Paste and drop are handled by the extension's built-in plugin
        onUpload: async (file: File) => {
          const src = await uploadFileRef.current(file);
          return { src, 'data-keep-ratio': true };
        }
      }),
      TableKit.configure({
        table: { resizable: false, renderWrapper: true, cellMinWidth: 50 }
      })
    ],
    content: '',
    onUpdate: () => setIsDirty(true)
  });

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

  const [selectedNote, setSelectedNote] = useState<any>(undefined);

  const loadNote = useCallback(
    (noteId: number) => {
      const note = notesQuery.data?.find((note: any) => note.pk === noteId);
      setSelectedNote(note);

      if (editor) {
        // Pass emitUpdate:false to avoid triggering dirty state when loading content
        editor.commands.setContent(
          note ? DOMPurify.sanitize(note.content ?? '') : '',
          { emitUpdate: false }
        );
      }

      setIsDirty(false);
    },
    [editor, notesQuery.data]
  );

  useEffect(() => {
    loadNote(selectedNoteId ?? -1);
  }, [editor, selectedNoteId, notesQuery.data]);

  // Adjust the note selection
  useEffect(() => {
    if (!notesQuery.data) return;

    const stillExists =
      selectedNoteId &&
      notesQuery.data.some((note: any) => note.pk === selectedNoteId);
    if (stillExists) return;

    const paramSlug = searchParams.get('note');
    const fromParam =
      paramSlug &&
      notesQuery.data.find(
        (note: any) => identifierString(note.title ?? '') === paramSlug
      );

    if (fromParam) {
      setSelectedNoteId(fromParam.pk);
      return;
    }

    const primary = notesQuery.data.find((note: any) => note.primary);
    setSelectedNoteId((primary ?? notesQuery.data[0])?.pk ?? undefined);
  }, [notesQuery.data]);

  const canEdit = useMemo(
    () =>
      user.hasChangePermission(modelType) &&
      notesQuery.isFetched &&
      notesQuery.isSuccess &&
      !!notesQuery.data,
    [user, modelType, notesQuery]
  );

  const isInTable = useEditorState({
    editor,
    selector: ({ editor: e }) => e?.isActive('table') ?? false
  });

  // Sync editor editable state when permissions change
  useEffect(() => {
    editor?.setEditable(canEdit);
  }, [editor, canEdit]);

  const hasNotes = useMemo(() => {
    return notesQuery.data && notesQuery.data.length > 0;
  }, [notesQuery.data]);

  const noteFields = useNoteFields({ modelType: modelType, modelId: modelId });

  const createNote = useCreateApiFormModal({
    title: t`Add Note`,
    fields: noteFields,
    url: apiUrl(ApiEndpoints.note_list),
    method: 'POST',
    successMessage: null,
    onFormSuccess: (response: any) => {
      notesQuery.refetch().then(() => {
        setSelectedNoteId(response.pk);
      });
    }
  });

  const deleteNote = useDeleteApiFormModal({
    title: t`Delete Note`,
    url: apiUrl(ApiEndpoints.note_list),
    pk: selectedNoteId,
    onFormSuccess: () => {
      setSelectedNoteId(undefined);
      notesQuery.refetch();
    }
  });

  const editNote = useEditApiFormModal({
    title: t`Edit Note`,
    fields: noteFields,
    url: apiUrl(ApiEndpoints.note_list),
    pk: selectedNoteId,
    onFormSuccess: (response: any) => {
      notesQuery.refetch().then(() => {
        setSelectedNoteId(response.pk);
      });
    }
  });

  const reloadNote = useCallback(() => {
    loadNote(selectedNoteId ?? -1);
  }, [selectedNoteId, loadNote]);

  const saveNote = useCallback(() => {
    if (!selectedNoteId || !editor) {
      return;
    }

    const cleanHtml = DOMPurify.sanitize(editor.getHTML());

    const url = apiUrl(ApiEndpoints.note_list, selectedNoteId);

    notifications.hide('note-update-status');

    api
      .patch(url, { content: cleanHtml })
      .then(() => {
        setIsDirty(false);
        notifications.show({
          title: t`Success`,
          message: t`Note updated`,
          color: 'green',
          id: 'note-update-status',
          autoClose: 2000
        });
      })
      .catch((error) => {
        notifications.show({
          title: t`Error`,
          message: t`Failed to update note: ${error.message}`,
          color: 'red',
          id: 'note-update-status',
          autoClose: 2000
        });
      })
      .finally(() => {
        notesQuery.refetch();
      });
  }, [selectedNoteId, editor, setIsDirty]);

  useHotkeys([['mod+s', saveNote]]);

  const handleImageUpload = useCallback(
    async (file: File | null) => {
      if (!file || !editor) return;
      try {
        const src = await uploadFile(file);
        editor
          .chain()
          .focus()
          .setResizableImage({ src, 'data-keep-ratio': true })
          .run();
      } catch {
        notifications.show({
          title: t`Error`,
          message: t`Failed to upload image`,
          color: 'red',
          autoClose: 2000
        });
      }
    },
    [editor, uploadFile]
  );

  return (
    <>
      {createNote.modal}
      {deleteNote.modal}
      {editNote.modal}
      <Flex align='left' gap={5}>
        <Box style={{ flex: 1 }}>
          <Stack gap={5}>
            {selectedNote && (
              <Paper p='xs' shadow='sm' withBorder>
                <Group justify='space-between'>
                  <Group justify='left' gap='lg'>
                    <NoteInfoHover note={selectedNote} />
                    <Text fw='bold'>{selectedNote?.title}</Text>
                    <Text size='sm'>{selectedNote?.description}</Text>
                  </Group>
                  {canEdit && (
                    <Group justify='right' gap='xs'>
                      {isDirty && (
                        <Badge color='yellow'>{t`Unsaved Changes`}</Badge>
                      )}
                      {isDirty && (
                        <Tooltip label={t`Save Notes (Ctrl+S)`}>
                          <ActionIcon
                            variant='transparent'
                            color={'green'}
                            onClick={saveNote}
                            disabled={!canEdit || !isDirty}
                          >
                            <IconDeviceFloppy />
                          </ActionIcon>
                        </Tooltip>
                      )}
                      {isDirty && (
                        <Tooltip label={t`Reset Notes`}>
                          <ActionIcon
                            variant='transparent'
                            onClick={reloadNote}
                            disabled={!canEdit || !isDirty}
                          >
                            <IconReload />
                          </ActionIcon>
                        </Tooltip>
                      )}
                      <OptionsActionDropdown
                        tooltip={t`Note Actions`}
                        actions={[
                          EditItemAction({
                            hidden:
                              !selectedNote ||
                              !user.hasChangePermission(modelType),
                            onClick: () => {
                              editNote.open();
                            }
                          }),
                          DeleteItemAction({
                            hidden:
                              !selectedNote ||
                              !user.hasDeletePermission(modelType),
                            onClick: () => {
                              deleteNote.open();
                            }
                          })
                        ]}
                      />
                    </Group>
                  )}
                </Group>
              </Paper>
            )}
            <Paper p='xs' shadow='sm' withBorder>
              {hasNotes ? (
                <RichTextEditor
                  variant='subtle'
                  editor={editor}
                  style={{ minHeight: '400px' }}
                >
                  {canEdit && (
                    <RichTextEditor.Toolbar sticky>
                      <RichTextEditor.ControlsGroup>
                        <RichTextEditor.Bold />
                        <RichTextEditor.Italic />
                        <RichTextEditor.Underline />
                        <RichTextEditor.Strikethrough />
                        <RichTextEditor.ClearFormatting />
                        <RichTextEditor.Code />
                        <RichTextEditor.CodeBlock />
                      </RichTextEditor.ControlsGroup>
                      <RichTextEditor.ControlsGroup>
                        <RichTextEditor.H1 />
                        <RichTextEditor.H2 />
                        <RichTextEditor.H3 />
                        <RichTextEditor.H4 />
                      </RichTextEditor.ControlsGroup>
                      <RichTextEditor.ControlsGroup>
                        <RichTextEditor.Blockquote />
                        <RichTextEditor.Hr />
                        <RichTextEditor.BulletList />
                        <RichTextEditor.OrderedList />
                      </RichTextEditor.ControlsGroup>
                      <RichTextEditor.ControlsGroup>
                        <RichTextEditor.Link />
                        <RichTextEditor.Unlink />
                      </RichTextEditor.ControlsGroup>
                      <RichTextEditor.ControlsGroup>
                        <RichTextEditor.Undo />
                        <RichTextEditor.Redo />
                      </RichTextEditor.ControlsGroup>
                      <RichTextEditor.ControlsGroup>
                        <FileButton
                          onChange={handleImageUpload}
                          accept='image/*'
                        >
                          {(props) => (
                            <Tooltip label={t`Upload Image`}>
                              <ActionIcon
                                variant='default'
                                size='sm'
                                {...props}
                              >
                                <IconPhoto size='0.9rem' />
                              </ActionIcon>
                            </Tooltip>
                          )}
                        </FileButton>
                      </RichTextEditor.ControlsGroup>
                      <RichTextEditor.ControlsGroup>
                        <RichTextEditor.Control
                          onClick={() =>
                            editor
                              ?.chain()
                              .focus()
                              .insertTable({
                                rows: 3,
                                cols: 3,
                                withHeaderRow: true
                              })
                              .run()
                          }
                          aria-label={t`Insert table`}
                          title={t`Insert table`}
                        >
                          <IconTablePlus size='0.9rem' />
                        </RichTextEditor.Control>
                        <RichTextEditor.Control
                          disabled={!isInTable}
                          onClick={() =>
                            editor?.chain().focus().addColumnBefore().run()
                          }
                          aria-label={t`Add column before`}
                          title={t`Add column before`}
                        >
                          <IconColumnInsertLeft size='0.9rem' />
                        </RichTextEditor.Control>
                        <RichTextEditor.Control
                          disabled={!isInTable}
                          onClick={() =>
                            editor?.chain().focus().addColumnAfter().run()
                          }
                          aria-label={t`Add column after`}
                          title={t`Add column after`}
                        >
                          <IconColumnInsertRight size='0.9rem' />
                        </RichTextEditor.Control>
                        <RichTextEditor.Control
                          disabled={!isInTable}
                          onClick={() =>
                            editor?.chain().focus().deleteColumn().run()
                          }
                          aria-label={t`Delete column`}
                          title={t`Delete column`}
                        >
                          <IconColumnRemove size='0.9rem' />
                        </RichTextEditor.Control>
                        <RichTextEditor.Control
                          disabled={!isInTable}
                          onClick={() =>
                            editor?.chain().focus().addRowBefore().run()
                          }
                          aria-label={t`Add row before`}
                          title={t`Add row before`}
                        >
                          <IconRowInsertTop size='0.9rem' />
                        </RichTextEditor.Control>
                        <RichTextEditor.Control
                          disabled={!isInTable}
                          onClick={() =>
                            editor?.chain().focus().addRowAfter().run()
                          }
                          aria-label={t`Add row after`}
                          title={t`Add row after`}
                        >
                          <IconRowInsertBottom size='0.9rem' />
                        </RichTextEditor.Control>
                        <RichTextEditor.Control
                          disabled={!isInTable}
                          onClick={() =>
                            editor?.chain().focus().deleteRow().run()
                          }
                          aria-label={t`Delete row`}
                          title={t`Delete row`}
                        >
                          <IconRowRemove size='0.9rem' />
                        </RichTextEditor.Control>
                        <RichTextEditor.Control
                          disabled={!isInTable}
                          onClick={() =>
                            editor?.chain().focus().toggleHeaderRow().run()
                          }
                          aria-label={t`Toggle header row`}
                          title={t`Toggle header row`}
                        >
                          <IconTableRow size='0.9rem' />
                        </RichTextEditor.Control>
                        <RichTextEditor.Control
                          disabled={!isInTable}
                          onClick={() =>
                            editor?.chain().focus().deleteTable().run()
                          }
                          aria-label={t`Delete table`}
                          title={t`Delete table`}
                        >
                          <IconTableOff size='0.9rem' />
                        </RichTextEditor.Control>
                      </RichTextEditor.ControlsGroup>
                    </RichTextEditor.Toolbar>
                  )}
                  <RichTextEditor.Content />
                </RichTextEditor>
              ) : (
                <Alert title={t`Notes`} icon={<IconInfoCircle />}>
                  {t`There are no notes yet for this item.`}
                </Alert>
              )}
            </Paper>
          </Stack>
        </Box>
        <Paper p='xs' shadow='sm' withBorder style={{ width: '200px' }}>
          <Stack gap='xs'>
            <Button
              color='green'
              leftSection={<IconCirclePlus />}
              onClick={createNote.open}
              // disabled={!canEdit || isDirty}
            >
              {t`Add Note`}
            </Button>

            <Tabs
              orientation='vertical'
              placement='right'
              value={selectedNoteId?.toString()}
            >
              <Tabs.List style={{ width: '100%' }}>
                {notesQuery.data?.map((note: any) => (
                  <Tabs.Tab
                    key={note.pk}
                    disabled={isDirty}
                    value={note.pk?.toString()}
                    onClick={() => {
                      setSelectedNoteId(note.pk);
                      setSearchParams(
                        (prev) => {
                          prev.set('note', identifierString(note.title ?? ''));
                          return prev;
                        },
                        { replace: true }
                      );
                    }}
                  >
                    <Group gap='xs' wrap='nowrap' justify='space-between'>
                      <Text size='sm'>{note.title}</Text>
                      {note.primary && (
                        <ActionIcon
                          size='xs'
                          color='yellow'
                          variant='transparent'
                        >
                          <IconStar />
                        </ActionIcon>
                      )}
                    </Group>
                  </Tabs.Tab>
                ))}
              </Tabs.List>
            </Tabs>
          </Stack>
        </Paper>
      </Flex>
    </>
  );
}
