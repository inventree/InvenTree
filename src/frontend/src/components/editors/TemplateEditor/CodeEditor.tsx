import { liquid } from '@codemirror/lang-liquid';
import { t } from '@lingui/macro';
import { IconCode } from '@tabler/icons-react';
import { vscodeDark } from '@uiw/codemirror-theme-vscode';
import { EditorView, hoverTooltip, useCodeMirror } from '@uiw/react-codemirror';
import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState
} from 'react';

import { Editor, EditorComponent } from './TemplateEditor';

type Tag = {
  label: string;
  description: string;
  args: string[];
  kwargs: { [name: string]: string };
  returns: string;
};

const tags: Tag[] = [
  {
    label: 'qrcode',
    description: 'Generate a QR code image',
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
    description: 'Generate a barcode image',
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

  const argsStr = tag.args
    .map((arg) => `  - <code style="color: #9cdcfe;">${arg}</code>`)
    .join('\n');

  const kwargsStr = Object.entries(tag.kwargs)
    .map(
      ([name, description]) =>
        `  - <code style="color: #9cdcfe;">${name}</code>: <small>${description}</small>`
    )
    .join('\n');

  dom.innerHTML = `Name: <code style="color: #4ec9b0;">${tag.label}</code>
<small>${tag.description}</small>
Arguments:
${argsStr}
Keyword arguments:
${kwargsStr}
Returns: <small>${tag.returns}</small>`;

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
  tooltips,
  EditorView.theme({
    '&.cm-editor': {
      height: '100%'
    }
  })
];

const CodeEditorComponent: EditorComponent = forwardRef((props, ref) => {
  const editor = useRef<HTMLDivElement | null>(null);
  const [code, setCode] = useState('');
  const { setContainer } = useCodeMirror({
    container: editor.current,
    extensions,
    value: code,
    onChange: (value) => setCode(value),
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

  return (
    <div style={{ display: 'flex', flex: '1', position: 'relative' }}>
      <div
        style={{ position: 'absolute', top: 0, bottom: 0, left: 0, right: 0 }}
        ref={editor}
      ></div>
    </div>
  );
});

export const CodeEditor: Editor = {
  key: 'code',
  name: t`Code`,
  icon: IconCode,
  component: CodeEditorComponent
};
