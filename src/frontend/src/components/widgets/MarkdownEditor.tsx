import 'easymde/dist/easymde.min.css';
import { ReactNode } from 'react';
import { useState } from 'react';
import SimpleMDE from 'react-simplemde-editor';

/**
 * Markdon editor component. Uses react-simplemde-editor
 */
export function MarkdownEditor({
  url,
  data
}: {
  url: string;
  data?: string;
}): ReactNode {
  const [value, setValue] = useState(data);

  return <SimpleMDE value={value} onChange={(v: string) => setValue(v)} />;
}
