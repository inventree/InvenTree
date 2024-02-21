import { langs } from '@uiw/codemirror-extensions-langs';
import { vscodeDark } from '@uiw/codemirror-theme-vscode';
import { useCodeMirror } from '@uiw/react-codemirror';
import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState
} from 'react';

import { CodeEditorComponent } from '.';

const extensions = [langs.html()];

export const CodeEditor: CodeEditorComponent = forwardRef((props, ref) => {
  const editor = useRef<HTMLDivElement | null>(null);
  const [code, setCode] = useState('');
  const { setContainer } = useCodeMirror({
    container: editor.current,
    extensions,
    value: code,
    onChange: (value) => setCode(value),
    height: '70vh',
    theme: vscodeDark
  });

  useImperativeHandle(ref, () => ({
    setCode: (code) => setCode(code),
    getCode: () => code
  }));

  useEffect(() => {
    if (editor.current) {
      setContainer(editor.current);
    }
  }, [editor.current]);

  return <div ref={editor}></div>;
});
