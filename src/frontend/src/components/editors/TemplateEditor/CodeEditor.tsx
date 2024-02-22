import { liquid } from '@codemirror/lang-liquid';
import { vscodeDark } from '@uiw/codemirror-theme-vscode';
import { hoverTooltip, useCodeMirror } from '@uiw/react-codemirror';
import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState
} from 'react';

import { EditorComponent } from './TemplateEditor';

type Tag = {
  label: string;
  args: string[];
  kwargs: { [name: string]: string };
  returns: string;
};

const tags: Tag[] = [
  {
    label: 'qrcode',
    args: ['data'],
    kwargs: {
      fill_color: 'Fill color (default = black)',
      back_color: 'Background color (default = white)',
      version: 'Version (default = 1)',
      box_size: 'Box size (default = 20)',
      border: 'Border width (default = 1)',
      format: 'Format (default = PNG)'
    },
    returns: 'base64 encoded qr code image data'
  },
  {
    label: 'barcode',
    args: ['data'],
    kwargs: {
      barcode_class: 'Barcode code',
      type: 'Barcode type (default = code128)',
      format: 'Format (default = PNG)'
    },
    returns: 'base64 encoded barcode image data'
  }
];
const tagsMap = Object.fromEntries(tags.map((tag) => [tag.label, tag]));

const renderHelp = (tag: Tag) => {
  const dom = document.createElement('div');
  dom.style.whiteSpace = 'pre-line';
  dom.style.width = '400px';
  dom.style.padding = '5px';
  dom.style.height = '200px';
  dom.style.overflowY = 'scroll';
  dom.style.border = '1px solid #000';
  dom.innerHTML = `Name: <code style="color: #4ec9b0;">${tag.label}</code>
Arguments:
${tag.args
  .map((arg) => `  - <code style="color: #9cdcfe;">${arg}</code>`)
  .join('\n')}
Keyword arguments:
${Object.entries(tag.kwargs)
  .map(
    ([name, description]) =>
      `  - <code style="color: #9cdcfe;">${name}</code>: ${description}`
  )
  .join('\n')}
Returns: ${tag.returns}`;
  return dom;
};

const tooltips = hoverTooltip((view, pos, side) => {
  // extract the word at the current hover position into the variable text
  let { from, to, text } = view.state.doc.lineAt(pos);
  let start = pos,
    end = pos;
  while (start > from && /\w/.test(text[start - from - 1])) start--;
  while (end < to && /\w/.test(text[end - from])) end++;
  if ((start == pos && side < 0) || (end == pos && side > 0)) return null;
  text = text.slice(start - from, end - from);

  if (!(text in tagsMap)) return null;
  return {
    pos: start,
    end,
    above: true,
    create(view) {
      return { dom: renderHelp(tagsMap[text]) };
    }
  };
});

const extensions = [
  liquid({
    tags: Object.values(tagsMap).map((tag) => {
      return {
        label: tag.label,
        type: 'function',
        info: () => renderHelp(tag),
        boost: 99
      };
    })
  }),
  tooltips
];

export const CodeEditor: EditorComponent = forwardRef((props, ref) => {
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
