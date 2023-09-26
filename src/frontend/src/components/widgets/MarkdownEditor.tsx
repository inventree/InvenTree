import { t } from '@lingui/macro';
import { showNotification } from '@mantine/notifications';
import EasyMDE from 'easymde';
import 'easymde/dist/easymde.min.css';
import { ReactNode, useCallback, useMemo } from 'react';
import { useState } from 'react';
import SimpleMDE from 'react-simplemde-editor';

import { api } from '../../App';

/**
 * Markdon editor component. Uses react-simplemde-editor
 */
export function MarkdownEditor({
  data,
  allowEdit,
  saveValue
}: {
  data?: string;
  allowEdit?: boolean;
  saveValue?: (value: string) => void;
}): ReactNode {
  const [value, setValue] = useState(data);

  // Construct markdown editor options
  const options = useMemo(() => {
    // Custom set of toolbar icons for the editor
    let icons: any[] = ['preview', 'side-by-side'];

    if (allowEdit) {
      icons.push(
        '|',

        // Heading icons
        'heading-1',
        'heading-2',
        'heading-3',
        '|',

        // Font styles
        'bold',
        'italic',
        'strikethrough',
        '|',

        // Text formatting
        'unordered-list',
        'ordered-list',
        'code',
        'quote',
        '|',

        // Link and image icons
        'table',
        'link',
        'image'
      );
    }

    if (allowEdit) {
      icons.push(
        '|',

        // Save button
        {
          name: 'save',
          action: (editor: EasyMDE) => {
            if (saveValue) {
              saveValue(editor.value());
            }
          },
          className: 'fa fa-save',
          title: t`Save`
        }
      );
    }

    return {
      minHeight: '400px',
      toolbar: icons,
      sideBySideFullscreen: false,
      uploadImage: allowEdit,
      imagePathAbsolute: true,
      imageUploadFunction: (
        file: File,
        onSuccess: (url: string) => void,
        onError: (error: string) => void
      ) => {
        api
          .post(
            '/notes-image-upload/',
            {
              image: file
            },
            {
              headers: {
                'Content-Type': 'multipart/form-data'
              }
            }
          )
          .then((response) => {
            if (response.data?.image) {
              onSuccess(response.data.image);
            }
          })
          .catch((error) => {
            showNotification({
              title: t`Error`,
              message: t`Failed to upload image`,
              color: 'red'
            });
            onError(error);
          });
      }
    };
  }, [allowEdit]);

  return (
    <SimpleMDE
      value={value}
      options={options}
      onChange={(v: string) => setValue(v)}
    />
  );
}

/**
 * Custom implementation of the MarkdownEditor widget for editing notes.
 * Includes a callback hook for saving the notes to the server.
 */
export function NotesEditor({
  url,
  data,
  allowEdit
}: {
  url: string;
  data?: string;
  allowEdit?: boolean;
}): ReactNode {
  // Callback function to upload data to the server
  const uploadData = useCallback((value: string) => {
    api
      .patch(url, { notes: value })
      .then((response) => {
        showNotification({
          title: t`Success`,
          message: t`Notes saved`,
          color: 'green'
        });
        return response;
      })
      .catch((error) => {
        showNotification({
          title: t`Error`,
          message: t`Failed to save notes`,
          color: 'red'
        });
        return error;
      });
  }, []);

  return (
    <MarkdownEditor data={data} allowEdit={allowEdit} saveValue={uploadData} />
  );
}
