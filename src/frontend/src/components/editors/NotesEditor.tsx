import { t } from '@lingui/core/macro';
import { useHotkeys } from '@mantine/hooks';
import { notifications } from '@mantine/notifications';
import { useQuery } from '@tanstack/react-query';
import DOMPurify from 'dompurify';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import type { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import { useApi } from '../../contexts/ApiContext';

import '@blocknote/core/fonts/inter.css';
import { BlockNoteView } from '@blocknote/mantine';
import '@blocknote/mantine/style.css';
import { useCreateBlockNote } from '@blocknote/react';
import {
  ActionIcon,
  Alert,
  Badge,
  Box,
  Button,
  Flex,
  Group,
  Paper,
  Stack,
  Tabs,
  Text,
  Tooltip
} from '@mantine/core';
import {
  IconCirclePlus,
  IconDeviceFloppy,
  IconInfoCircle,
  IconReload,
  IconStar
} from '@tabler/icons-react';
import { useNoteFields } from '../../forms/CommonForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useUserState } from '../../states/UserState';
import {
  DeleteItemAction,
  EditItemAction,
  OptionsActionDropdown
} from '../items/ActionDropdown';

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

  const editor = useCreateBlockNote();

  const [isDirty, setIsDirty] = useState(false);

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

  useEffect(() => {
    return editor.onChange(() => setIsDirty(true));
  }, [editor]);

  const loadNote = useCallback(
    (noteId: number) => {
      const note = notesQuery.data?.find((note: any) => note.pk === noteId);

      if (note) {
        const blocks = editor.tryParseHTMLToBlocks(note.content ?? '');

        if (blocks) {
          editor.replaceBlocks(editor.document, blocks);
        } else {
          editor.replaceBlocks(editor.document, []);
        }
      }

      setIsDirty(false);
    },
    [editor, notesQuery.data]
  );

  useEffect(() => {
    loadNote(selectedNote ?? -1);
  }, [editor, selectedNote, notesQuery.data]);

  // Adjust the note selection
  useEffect(() => {
    if (!notesQuery.data) return;

    const stillExists =
      selectedNote &&
      notesQuery.data.some((note: any) => note.pk === selectedNote);
    if (stillExists) return;

    const primary = notesQuery.data.find((note: any) => note.primary);
    setSelectedNote((primary ?? notesQuery.data[0])?.pk ?? undefined);
  }, [notesQuery.data]);

  const canEdit = useMemo(
    () =>
      user.hasChangePermission(modelType) &&
      notesQuery.isFetched &&
      notesQuery.isSuccess &&
      !!notesQuery.data,
    [user, modelType, notesQuery]
  );

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
        // Select the newly created note
        setSelectedNote(response.pk);
      });
    }
  });

  const deleteNote = useDeleteApiFormModal({
    title: t`Delete Note`,
    url: apiUrl(ApiEndpoints.note_list),
    pk: selectedNote,
    onFormSuccess: () => {
      setSelectedNote(undefined);
      notesQuery.refetch();
    }
  });

  const editNote = useEditApiFormModal({
    title: t`Edit Note`,
    fields: noteFields,
    url: apiUrl(ApiEndpoints.note_list),
    pk: selectedNote,
    onFormSuccess: (response: any) => {
      notesQuery.refetch().then(() => {
        // Select the updated note
        setSelectedNote(response.pk);
      });
    }
  });

  const reloadNote = useCallback(() => {
    loadNote(selectedNote ?? -1);
  }, [selectedNote, loadNote]);

  const saveNote = useCallback(() => {
    if (!selectedNote) {
      return;
    }

    const blocks = editor.document;
    const html = editor.blocksToHTMLLossy(blocks);
    const cleanHtml = DOMPurify.sanitize(html);

    // Sanitize the HTML content before sending to the server (or ensure it's sanitized on the back-end)

    if (selectedNote) {
      const url = apiUrl(ApiEndpoints.note_list, selectedNote);

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
    }
  }, [selectedNote, editor, setIsDirty]);

  useHotkeys([['mod+s', saveNote]]);

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
                    <Text>Note Title Here</Text>
                    <Text size='sm'>Note description here</Text>
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
                <Stack gap='xs'>
                  <BlockNoteView
                    editor={editor}
                    editable={canEdit}
                    style={{ minHeight: '400px' }}
                  />
                </Stack>
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
              disabled={!canEdit || isDirty}
            >
              {t`Add Note`}
            </Button>

            <Tabs
              orientation='vertical'
              placement='right'
              value={selectedNote?.toString()}
            >
              <Tabs.List style={{ width: '100%' }}>
                {notesQuery.data?.map((note: any) => (
                  <Tabs.Tab
                    key={note.pk}
                    disabled={isDirty}
                    value={note.pk?.toString()}
                    onClick={() => setSelectedNote(note.pk)}
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
