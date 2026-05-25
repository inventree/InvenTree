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
import * as BlockNoteLocales from '@blocknote/core/locales';
import { useCreateBlockNote } from '@blocknote/react';

import {
  ActionIcon,
  Alert,
  Badge,
  Box,
  Button,
  Flex,
  Group,
  HoverCard,
  Paper,
  Stack,
  Tabs,
  Text,
  Tooltip,
  useMantineColorScheme
} from '@mantine/core';
import {
  IconCirclePlus,
  IconDeviceFloppy,
  IconInfoCircle,
  IconReload,
  IconStar
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
  const [language] = useLocalState(useShallow((s) => [s.language]));
  const { colorScheme } = useMantineColorScheme();

  const editor = useCreateBlockNote({
    dictionary:
      BlockNoteLocales[language as keyof typeof BlockNoteLocales] ||
      BlockNoteLocales.en
  });

  const [isDirty, setIsDirty] = useState(false);

  // The ID of the selected note
  const [selectedNoteId, setSelectedNoteId] = useState<number | undefined>(
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

  const [selectedNote, setSelectedNote] = useState<any>(undefined);

  const loadNote = useCallback(
    (noteId: number) => {
      const note = notesQuery.data?.find((note: any) => note.pk === noteId);

      setSelectedNote(note);

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
    loadNote(selectedNoteId ?? -1);
  }, [editor, selectedNoteId, notesQuery.data]);

  // Adjust the note selection
  useEffect(() => {
    if (!notesQuery.data) return;

    const stillExists =
      selectedNoteId &&
      notesQuery.data.some((note: any) => note.pk === selectedNoteId);
    if (stillExists) return;

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
        // Select the updated note
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

    const blocks = editor.document;
    const html = editor.blocksToHTMLLossy(blocks);
    const cleanHtml = DOMPurify.sanitize(html);

    // Sanitize the HTML content before sending to the server (or ensure it's sanitized on the back-end)

    if (selectedNoteId) {
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
    }
  }, [selectedNoteId, editor, setIsDirty]);

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
                <Stack gap='xs'>
                  <BlockNoteView
                    editor={editor}
                    editable={canEdit}
                    theme={colorScheme === 'dark' ? 'dark' : 'light'}
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
              value={selectedNoteId?.toString()}
            >
              <Tabs.List style={{ width: '100%' }}>
                {notesQuery.data?.map((note: any) => (
                  <Tabs.Tab
                    key={note.pk}
                    disabled={isDirty}
                    value={note.pk?.toString()}
                    onClick={() => setSelectedNoteId(note.pk)}
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
