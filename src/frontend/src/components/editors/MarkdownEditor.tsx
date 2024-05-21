import {
  BlockTypeSelect,
  BoldItalicUnderlineToggles,
  CodeToggle,
  CreateLink,
  InsertAdmonition,
  InsertCodeBlock,
  InsertImage,
  InsertTable,
  InsertThematicBreak,
  ListsToggle,
  MDXEditor,
  type MDXEditorMethods,
  type MDXEditorProps,
  Separator,
  UndoRedo,
  headingsPlugin,
  imagePlugin,
  listsPlugin,
  markdownShortcutPlugin,
  quotePlugin,
  thematicBreakPlugin,
  toolbarPlugin
} from '@mdxeditor/editor';
import '@mdxeditor/editor/style.css';
import { type ForwardedRef, useCallback } from 'react';

import { api } from '../../App';

async function uploadNotesImage(image: File): Promise<string> {
  const formData = new FormData();
  formData.append('file', image);

  // TODO: Add other information here such as the model instance

  const response = await api.post('/notes/images/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });

  return response.data.url;
}

export default function MarkdownEditor({}: {}) {
  const imageUploadHandler = useCallback((image: File): Promise<string> => {
    // TODO: Add upload handler for images
    return uploadNotesImage(image);
  }, []);

  return (
    <MDXEditor
      markdown="hello world"
      plugins={[
        headingsPlugin(),
        listsPlugin(),
        markdownShortcutPlugin(),
        quotePlugin(),
        imagePlugin({ imageUploadHandler }),
        thematicBreakPlugin(),
        toolbarPlugin({
          toolbarContents: () => (
            <>
              {' '}
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
              <InsertCodeBlock />
              <InsertAdmonition />
              <InsertThematicBreak />
            </>
          )
        })
      ]}
    />
  );
}
