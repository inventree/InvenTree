import {
  type AppendMessage,
  AssistantRuntimeProvider,
  type AttachmentAdapter,
  AttachmentPrimitive,
  ComposerPrimitive,
  MessagePrimitive,
  type PendingAttachment,
  ThreadPrimitive,
  useAui,
  useAuiEvent,
  useAuiState,
  useExternalStoreRuntime
} from '@assistant-ui/react';
import {
  type CodeHeaderProps,
  MarkdownTextPrimitive
} from '@assistant-ui/react-markdown';
import {
  ActionIcon,
  Alert,
  Badge,
  Button,
  Group,
  Loader,
  Menu,
  Modal,
  Progress,
  Text,
  TextInput,
  Tooltip
} from '@mantine/core';
import {
  IconArrowDown,
  IconArrowLeft,
  IconArrowUp,
  IconCheck,
  IconCopy,
  IconDots,
  IconDownload,
  IconFile,
  IconPaperclip,
  IconPlayerStop,
  IconRefresh,
  IconX
} from '@tabler/icons-react';
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState
} from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import remarkGfm from 'remark-gfm';
import { useApi } from '../../contexts/ApiContext';
import { useUserState } from '../../states/UserState';
import {
  ASSISTANT_API,
  ATTACHMENT_ACCEPT,
  type AttachmentInfo,
  type BusinessReference,
  type HistoryMessage,
  type HistoryPage,
  type Submission,
  apiError,
  attachmentName,
  toMessage
} from './assistant-api';
import './assistant.css';

const FilesContext = createContext<{
  files: Map<string, AttachmentInfo>;
  progress: Map<string, number>;
  error: (text: string) => void;
}>({ files: new Map(), progress: new Map(), error: () => {} });
function protectedPath(url: string) {
  // File links are application-controlled. Never send session/token headers to arbitrary message URLs.
  const parsed = new URL(url, window.location.origin);
  if (!parsed.pathname.startsWith(`${ASSISTANT_API}attachments/`))
    throw new Error('附件地址无效');
  return parsed.pathname + parsed.search;
}
function useProtectedBlob(url?: string | null) {
  const api = useApi();
  const [blob, setBlob] = useState<string>();
  useEffect(() => {
    if (!url) return;
    const abort = new AbortController();
    let created: string | undefined;
    api
      .get(protectedPath(url), { responseType: 'blob', signal: abort.signal })
      .then(({ data }) => {
        created = URL.createObjectURL(data);
        setBlob(created);
      })
      .catch(() => {});
    return () => {
      abort.abort();
      if (created) URL.revokeObjectURL(created);
    };
  }, [url, api]);
  return blob;
}
function FileCard({ removable = false }: { removable?: boolean }) {
  const attachment = useAuiState((s) => s.attachment);
  const { files, progress, error } = useContext(FilesContext);
  const info = files.get(attachment.id);
  const preview = useProtectedBlob(info?.preview_url);
  const [opened, setOpened] = useState(false);
  const api = useApi();
  const upload = progress.get(attachment.id);
  const failed = attachment.status.type === 'incomplete';
  async function download() {
    if (!info) return;
    try {
      const { data } = await api.get(protectedPath(info.download_url), {
        responseType: 'blob'
      });
      const url = URL.createObjectURL(data);
      const a = document.createElement('a');
      a.href = url;
      a.download = attachment.name;
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (err) {
      error(apiError(err));
    }
  }
  return (
    <AttachmentPrimitive.Root className='partner-file'>
      {preview ? (
        <button
          className='partner-image-button'
          type='button'
          onClick={() => setOpened(true)}
          aria-label={`预览 ${attachment.name}`}
        >
          <img src={preview} alt={attachment.name} />
        </button>
      ) : (
        <IconFile size={24} aria-hidden />
      )}
      <div className='partner-file-info'>
        <AttachmentPrimitive.Name />
        <Text size='xs' c={failed ? 'red' : 'dimmed'}>
          {attachment.status.type === 'incomplete'
            ? attachment.status.message || '上传失败，请移除后重试'
            : attachment.status.type === 'running'
              ? `上传中 ${upload ?? attachment.status.progress ?? 0}%`
              : info
                ? `${(info.size / 1024).toFixed(1)} KB`
                : '附件'}
        </Text>
        {attachment.status.type === 'running' && (
          <Progress value={upload ?? 0} size='xs' aria-label='上传进度' />
        )}
        {info?.extraction_note && (
          <Text size='xs' c='orange' mt={4}>
            {info.extraction_note}
          </Text>
        )}
      </div>
      {info && (
        <ActionIcon
          variant='subtle'
          aria-label={`下载 ${attachment.name}`}
          onClick={download}
        >
          <IconDownload size={17} />
        </ActionIcon>
      )}
      {removable && (
        <AttachmentPrimitive.Remove asChild>
          <ActionIcon variant='subtle' aria-label={`移除 ${attachment.name}`}>
            <IconX size={17} />
          </ActionIcon>
        </AttachmentPrimitive.Remove>
      )}
      <Modal
        opened={opened}
        onClose={() => setOpened(false)}
        title={attachment.name}
        closeButtonProps={{ 'aria-label': '关闭图片预览' }}
        size='xl'
        centered
      >
        {preview && (
          <img
            src={preview}
            alt={attachment.name}
            style={{ width: '100%', objectFit: 'contain', maxHeight: '75vh' }}
          />
        )}
        <Button mt='sm' variant='light' onClick={download}>
          下载原图
        </Button>
      </Modal>
    </AttachmentPrimitive.Root>
  );
}
function SubmittedFile({ id }: { id: string }) {
  const { files } = useContext(FilesContext);
  const file = files.get(id);
  const preview = useProtectedBlob(file?.preview_url);
  const [opened, setOpened] = useState(false);
  if (!file) return null;
  return (
    <div className='partner-file'>
      {preview && (
        <button
          className='partner-image-button'
          type='button'
          aria-label={`预览 ${file.name}`}
          onClick={() => setOpened(true)}
        >
          <img src={preview} alt={file.name} />
        </button>
      )}
      <Text size='sm'>{attachmentName(file)}</Text>
      <Modal
        opened={opened}
        onClose={() => setOpened(false)}
        title={file.name}
        closeButtonProps={{ 'aria-label': '关闭图片预览' }}
        size='xl'
      >
        {preview && (
          <img src={preview} alt={file.name} style={{ width: '100%' }} />
        )}
      </Modal>
    </div>
  );
}
function SubmittedFiles({ ids }: { ids: string[] }) {
  return (
    <div className='partner-files'>
      {ids.map((id) => (
        <SubmittedFile key={id} id={id} />
      ))}
    </div>
  );
}
function UploadErrors() {
  const { error } = useContext(FilesContext);
  useAuiEvent('composer.attachmentAddError', (event) =>
    error(
      event.reason === 'not-accepted'
        ? '此文件类型暂不支持。可上传图片、PDF、Word、Excel 和文本资料。'
        : event.message
    )
  );
  return null;
}
function ComposerFile() {
  return <FileCard removable />;
}
function CodeHeader({ language, code }: CodeHeaderProps) {
  const [copied, setCopied] = useState(false);
  return (
    <div className='partner-code-header'>
      <span>{language || '代码'}</span>
      <button
        type='button'
        onClick={() =>
          navigator.clipboard.writeText(code).then(() => {
            setCopied(true);
            setTimeout(() => setCopied(false), 1800);
          })
        }
      >
        {copied ? '已复制' : '复制代码'}
      </button>
    </div>
  );
}
function Markdown() {
  return (
    <MarkdownTextPrimitive
      className='partner-markdown'
      remarkPlugins={[remarkGfm]}
      smooth={false}
      components={{
        CodeHeader,
        img: ({ alt }) => <span>[图片：{alt || '请查看附件'}]</span>,
        a: ({ href, children }) => (
          <a href={href} target='_blank' rel='noreferrer noopener'>
            {children}
          </a>
        )
      }}
    />
  );
}
function ChatMessage() {
  const message = useAuiState((s) => s.message);
  const [copied, setCopied] = useState(false);
  const refs = (message.metadata.custom?.references ||
    []) as BusinessReference[];
  const text = message.content
    .filter((part) => part.type === 'text')
    .map((part) => part.text)
    .join('\n');
  return (
    <MessagePrimitive.Root
      id={`partner-message-${message.id}`}
      className={`partner-message partner-message-${message.role}`}
      aria-label={message.role === 'user' ? '你的消息' : '工作伙伴消息'}
    >
      <Text size='xs' c='dimmed' mb={6}>
        {message.role === 'user' ? '你' : '工作伙伴'}
        {message.createdAt && (
          <time
            dateTime={message.createdAt.toISOString()}
            style={{ marginLeft: 10 }}
          >
            {message.createdAt.toLocaleString('zh-CN', {
              month: '2-digit',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit'
            })}
          </time>
        )}
      </Text>
      <MessagePrimitive.Parts components={{ Text: Markdown }} />
      {!!message.attachments?.length && (
        <div className='partner-files'>
          <MessagePrimitive.Attachments components={{ Attachment: FileCard }} />
        </div>
      )}
      {!!refs.length && (
        <Group gap={6} mt={6}>
          {refs.map((reference) => {
            const badge = (
              <Badge variant='light'>
                {reference.label ||
                  `${reference.object_type} #${reference.object_id}`}
              </Badge>
            );
            return reference.page_url ? (
              <Link
                key={`${reference.object_type}:${reference.object_id}`}
                to={reference.page_url}
              >
                {badge}
              </Link>
            ) : (
              <span key={`${reference.object_type}:${reference.object_id}`}>
                {badge}
              </span>
            );
          })}
        </Group>
      )}
      {text && (
        <Tooltip label={copied ? '已复制' : '复制消息'}>
          <ActionIcon
            className='partner-copy'
            variant='subtle'
            color='gray'
            size='sm'
            aria-label='复制消息'
            onClick={() =>
              navigator.clipboard.writeText(text).then(() => {
                setCopied(true);
                setTimeout(() => setCopied(false), 1800);
              })
            }
          >
            {copied ? <IconCheck size={14} /> : <IconCopy size={14} />}
          </ActionIcon>
        </Tooltip>
      )}
    </MessagePrimitive.Root>
  );
}
function Draft({
  draftKey,
  restoredFiles
}: { draftKey: string; restoredFiles: AttachmentInfo[] | null }) {
  const aui = useAui();
  const { files } = useContext(FilesContext);
  const text = useAuiState((state) => state.composer.text);
  const attachments = useAuiState((state) => state.composer.attachments);
  const didRestore = useRef(false);
  const [restored, setRestored] = useState(false);
  useEffect(() => {
    const draft = sessionStorage.getItem(draftKey);
    if (draft) aui.composer().setText(draft);
  }, [draftKey, aui]);
  useEffect(() => {
    sessionStorage.setItem(draftKey, text);
  }, [draftKey, text]);
  useEffect(() => {
    if (restoredFiles === null || didRestore.current) return;
    didRestore.current = true;
    void Promise.all(
      restoredFiles.map((file) =>
        aui.composer().addAttachment({
          id: file.id,
          name: attachmentName(file),
          type: file.mime_type.startsWith('image/') ? 'image' : 'document',
          contentType: file.mime_type,
          content: []
        })
      )
    ).then(() => setRestored(true));
  }, [restoredFiles, aui]);
  useEffect(() => {
    if (!restored) return;
    const metadata = attachments
      .map((attachment) => files.get(attachment.id))
      .filter((file): file is AttachmentInfo => !!file);
    sessionStorage.setItem(`${draftKey}:attachments`, JSON.stringify(metadata));
  }, [draftKey, restored, attachments, files]);
  return null;
}
export default function AssistantPage() {
  const api = useApi();
  const location = useLocation();
  const navigate = useNavigate();
  const userId = useUserState((state) => state.user?.pk);
  const [messages, setMessages] = useState<HistoryMessage[]>([]);
  const [page, setPage] = useState<HistoryPage>();
  const [loading, setLoading] = useState(true);
  const [findOpen, setFindOpen] = useState(false);
  const [findText, setFindText] = useState('');
  const [olderLoading, setOlderLoading] = useState(false);
  const [error, setError] = useState('');
  const [connectionError, setConnectionError] = useState('');
  const [online, setOnline] = useState(navigator.onLine);
  const [submissions, setSubmissions] = useState<
    {
      payload: Submission;
      status: 'sending' | 'queued' | 'failed';
      error?: string;
    }[]
  >([]);
  const draftKey = `cangxu-assistant-draft:${api.defaults.baseURL || window.location.origin}:${userId}`;
  const referenceDraftKey = `${draftKey}:references:${location.key}`;
  const [references, setReferences] = useState<BusinessReference[]>(() => {
    try {
      const saved = sessionStorage.getItem(referenceDraftKey);
      if (saved) {
        const value = JSON.parse(saved);
        if (Array.isArray(value)) return value.slice(0, 8);
      }
    } catch {
      // A malformed draft must not prevent opening the conversation.
    }
    return location.state?.references || [];
  });
  useEffect(() => {
    sessionStorage.setItem(referenceDraftKey, JSON.stringify(references));
  }, [referenceDraftKey, references]);
  const [files, setFiles] = useState(new Map<string, AttachmentInfo>());
  const [progress, setProgress] = useState(new Map<string, number>());
  const uploadSizes = useRef(new Map<string, number>());
  const uploadQueue = useRef<Promise<void>>(Promise.resolve());
  const [restoredFiles, setRestoredFiles] = useState<AttachmentInfo[] | null>(
    null
  );
  useEffect(() => {
    let cancelled = false;
    let candidates: unknown[] = [];
    try {
      const value = JSON.parse(
        sessionStorage.getItem(`${draftKey}:attachments`) || '[]'
      );
      if (Array.isArray(value)) candidates = value.slice(0, 8);
    } catch {
      /* Discard malformed local drafts. */
    }
    void Promise.all(
      candidates.map(async (candidate) => {
        const id = (candidate as AttachmentInfo)?.id;
        if (typeof id !== 'string' || !/^[a-f0-9-]{36}$/.test(id)) return null;
        try {
          const { data } = await api.get<AttachmentInfo>(
            `${ASSISTANT_API}attachments/${id}/`
          );
          return data.id === id && typeof data.mime_type === 'string'
            ? data
            : null;
        } catch {
          return null;
        }
      })
    ).then((results) => {
      if (cancelled) return;
      const valid: AttachmentInfo[] = [];
      let total = 0;
      for (const file of results)
        if (
          file &&
          file.size <= 20 * 1024 * 1024 &&
          total + file.size <= 40 * 1024 * 1024
        ) {
          valid.push(file);
          total += file.size;
          uploadSizes.current.set(file.id, file.size);
        }
      setFiles((current) => {
        const next = new Map(current);
        for (const file of valid) next.set(file.id, file);
        return next;
      });
      setRestoredFiles(valid);
    });
    return () => {
      cancelled = true;
    };
  }, [api, draftKey]);
  const cancelUploads = useRef(new Map<string, AbortController>());
  const mounted = useRef(true);
  const historyLoaded = useRef(false);
  const viewport = useRef<HTMLDivElement>(null);
  const refresh = useCallback(
    async (before?: number) => {
      try {
        const [history, status] = await Promise.all([
          api.get<HistoryPage>(`${ASSISTANT_API}messages/`, {
            params: { limit: 50, ...(before ? { before } : {}) },
            timeout: 15000
          }),
          api.get<NonNullable<HistoryPage['runtime_status']>>(
            `${ASSISTANT_API}status/`,
            { timeout: 15000 }
          )
        ]);
        const data = { ...history.data, runtime_status: status.data };
        if (!mounted.current) return;
        setMessages((existing) => {
          const merged = new Map(
            existing.map((item) => [String(item.id), item])
          );
          for (const item of data.items) merged.set(String(item.id), item);
          return [...merged.values()].sort(
            (a, b) => Number(a.id) - Number(b.id)
          );
        });
        setFiles((existing) => {
          const next = new Map(existing);
          for (const item of [...data.items, ...(data.pending || [])])
            for (const file of item.attachments || []) next.set(file.id, file);
          return next;
        });
        setPage((existing) =>
          before || !existing || !historyLoaded.current
            ? data
            : {
                ...data,
                next_before: existing.next_before,
                has_more: existing.has_more
              }
        );
        const accepted = new Set([
          ...data.items.map((m) => m.request_id),
          ...(data.pending || []).map((m) => m.request_id)
        ]);
        setSubmissions((current) =>
          current.filter((s) => !accepted.has(s.payload.client_request_id))
        );
        const last = data.items.at(-1);
        if (last)
          sessionStorage.setItem(
            `cangxu-assistant-read:${userId}`,
            String(last.id)
          );
        historyLoaded.current = true;
        setConnectionError('');
      } catch (err) {
        if (mounted.current) setConnectionError(apiError(err));
      } finally {
        if (mounted.current) setLoading(false);
      }
    },
    [api, userId]
  );
  useEffect(() => {
    mounted.current = true;
    let timer: ReturnType<typeof setTimeout>;
    async function poll() {
      await refresh();
      if (mounted.current)
        timer = setTimeout(poll, document.hidden ? 15000 : 2500);
    }
    void poll();
    const update = () => setOnline(navigator.onLine);
    window.addEventListener('online', update);
    window.addEventListener('offline', update);
    return () => {
      mounted.current = false;
      clearTimeout(timer);
      window.removeEventListener('online', update);
      window.removeEventListener('offline', update);
      for (const controller of cancelUploads.current.values())
        controller.abort();
    };
  }, [refresh]);
  const uploadAdapter = useMemo<AttachmentAdapter>(
    () => ({
      accept: ATTACHMENT_ACCEPT,
      async *add({ file }) {
        const id = crypto.randomUUID();
        const base: PendingAttachment = {
          id,
          file,
          name: file.name,
          type: file.type.startsWith('image/') ? 'image' : 'document',
          contentType: file.type,
          status: { type: 'running', reason: 'uploading', progress: 0 }
        };
        if (
          file.size > 20 * 1024 * 1024 ||
          uploadSizes.current.size >= 8 ||
          [...uploadSizes.current.values()].reduce((a, b) => a + b, 0) +
            file.size >
            40 * 1024 * 1024
        ) {
          yield {
            ...base,
            status: {
              type: 'incomplete',
              reason: 'error',
              message: '每次最多 8 个文件，单个 20 MB、合计 40 MB'
            }
          };
          return;
        }
        uploadSizes.current.set(id, file.size);
        const controller = new AbortController();
        cancelUploads.current.set(id, controller);
        const previousUpload = uploadQueue.current;
        let releaseUpload = () => {};
        uploadQueue.current = new Promise<void>((resolve) => {
          releaseUpload = resolve;
        });
        try {
          yield base;
          await previousUpload;
          if (controller.signal.aborted) return;
          const form = new FormData();
          form.append('file', file);
          form.append('client_upload_id', id);
          const upload = async () => {
            return await api.post<AttachmentInfo>(
              `${ASSISTANT_API}attachments/`,
              form,
              {
                timeout: 120000,
                signal: controller.signal,
                onUploadProgress: ({ loaded, total }) =>
                  setProgress((current) =>
                    new Map(current).set(
                      id,
                      total ? Math.round((loaded / total) * 100) : 0
                    )
                  )
              }
            );
          };
          let result: Awaited<ReturnType<typeof upload>> | undefined;
          for (let attempt = 0; attempt < 3; attempt++) {
            try {
              result = await upload();
              break;
            } catch (error) {
              const status = (error as { response?: { status?: number } })
                .response?.status;
              if (
                controller.signal.aborted ||
                attempt === 2 ||
                (status && status !== 500 && status !== 503)
              )
                throw error;
              await new Promise((resolve) =>
                setTimeout(resolve, 300 * (attempt + 1))
              );
            }
          }
          if (!result) throw new Error('Upload did not complete');
          const { data } = result;

          setFiles((current) =>
            new Map(current).set(id, data).set(data.id, data)
          );
          yield {
            ...base,
            status: { type: 'requires-action', reason: 'composer-send' }
          };
        } catch (err) {
          yield {
            ...base,
            status: {
              type: 'incomplete',
              reason: 'error',
              message: apiError(err)
            }
          };
        } finally {
          cancelUploads.current.delete(id);
          // A cancelled queued card must not let later uploads overtake
          // the file which is still using the network slot.
          void previousUpload.then(releaseUpload);
        }
      },
      async send(attachment) {
        return { ...attachment, status: { type: 'complete' }, content: [] };
      },
      async remove(attachment) {
        cancelUploads.current.get(attachment.id)?.abort();
        uploadSizes.current.delete(attachment.id);
        const info = files.get(attachment.id);
        if (info) await api.delete(`${ASSISTANT_API}attachments/${info.id}/`);
      }
    }),
    [api, files]
  );
  async function submit(payload: Submission, retry = false) {
    setSubmissions((current) => [
      ...current.filter(
        (s) => s.payload.client_request_id !== payload.client_request_id
      ),
      { payload, status: 'sending' }
    ]);
    try {
      await api.post(
        `${ASSISTANT_API}messages/`,
        { ...payload, ...(retry ? { retry: true } : {}) },
        { timeout: 15000 }
      );
      setSubmissions((current) =>
        current.map((s) =>
          s.payload.client_request_id === payload.client_request_id
            ? { ...s, status: 'queued' }
            : s
        )
      );
      await refresh();
    } catch (err) {
      setSubmissions((current) =>
        current.map((s) =>
          s.payload.client_request_id === payload.client_request_id
            ? { ...s, status: 'failed', error: apiError(err) }
            : s
        )
      );
    }
  }
  async function onNew(message: AppendMessage) {
    const payload: Submission = {
      client_request_id: crypto.randomUUID(),
      text: message.content
        .filter((part) => part.type === 'text')
        .map((part) => part.text)
        .join('\n'),
      attachments: (message.attachments || []).map(
        (file) => files.get(file.id)?.id || file.id
      ),
      references: references.map(({ object_type, object_id }) => ({
        object_type,
        object_id
      }))
    };
    setReferences([]);
    uploadSizes.current.clear();
    await submit(payload);
  }
  const running =
    page?.runtime_status?.reply_running ?? page?.reply_running ?? false;
  const displayMessages = page?.runtime_status?.live_message
    ? [...messages, page.runtime_status.live_message]
    : messages;
  const runtime = useExternalStoreRuntime({
    messages: displayMessages,
    convertMessage: toMessage,
    isLoading: loading,
    isRunning: running,
    onCancel: () => stop('reply'),
    // Pi owns the durable inbox. This bridge advertises follow-up support to
    // assistant-ui without adding a browser-owned queue or interrupting a run.
    queue: {
      items: [],
      steerItems: [],
      enqueue: (message) => {
        void onNew(message);
      },
      steer: (message) => {
        void onNew(message);
      },
      move: () => {
        throw new Error('后台已接收的交办不能在浏览器中重新排序');
      },
      edit: () => {
        throw new Error('请通过补充消息更正已接收的交办');
      },
      remove: () => {
        throw new Error('请使用停止操作取消正在执行的工作');
      }
    },
    onNew,
    adapters: { attachments: uploadAdapter }
  });
  async function stop(scope: 'reply' | 'all-writes' | 'all-background') {
    try {
      await api.post(`${ASSISTANT_API}controls/`, {
        client_request_id: crypto.randomUUID(),
        scope
      });
      await refresh();
    } catch (err) {
      setError(apiError(err));
    }
  }
  const context = useMemo(
    () => ({ files, progress, error: setError }),
    [files, progress]
  );
  return (
    <FilesContext.Provider value={context}>
      <AssistantRuntimeProvider runtime={runtime}>
        <UploadErrors />
        <Modal
          opened={findOpen}
          onClose={() => setFindOpen(false)}
          title='查找历史'
          closeButtonProps={{ 'aria-label': '关闭历史查找' }}
        >
          <TextInput
            aria-label='搜索对话'
            placeholder='搜索已载入的对话'
            value={findText}
            onChange={(event) => setFindText(event.currentTarget.value)}
          />
          <Text size='xs' c='dimmed' mt='xs'>
            搜索当前已载入的消息；需要时可在对话顶部加载更早记录。
          </Text>
          {findText.trim() &&
            messages
              .filter((message) =>
                message.text
                  .toLocaleLowerCase()
                  .includes(findText.toLocaleLowerCase())
              )
              .map((message) => (
                <Button
                  key={message.id}
                  variant='subtle'
                  fullWidth
                  mt='xs'
                  justify='flex-start'
                  onClick={() => {
                    setFindOpen(false);
                    setTimeout(
                      () =>
                        document
                          .getElementById(`partner-message-${message.id}`)
                          ?.scrollIntoView({ block: 'center' }),
                      100
                    );
                  }}
                >
                  {message.text.slice(0, 90)}
                </Button>
              ))}
        </Modal>
        <main className='partner-page' aria-label='工作伙伴对话'>
          <header className='partner-header'>
            <Group gap='sm'>
              <ActionIcon
                variant='subtle'
                aria-label='返回业务页面'
                onClick={() => navigate(location.state?.returnTo || '/cangxu/')}
              >
                <IconArrowLeft size={20} />
              </ActionIcon>
              <div>
                <Text fw={600}>工作伙伴</Text>
                <Text size='xs' c='dimmed' component='output'>
                  {!online
                    ? '离线 · 已交办的工作继续运行'
                    : loading
                      ? '正在连接…'
                      : connectionError
                        ? '连接暂时中断'
                        : running
                          ? '正在处理你的交办'
                          : page?.runtime_status?.is_running
                            ? '后台工作进行中'
                            : '同一个伙伴，持续推进工作'}
                </Text>
              </div>
            </Group>
            <Menu position='bottom-end'>
              <Menu.Target>
                <ActionIcon variant='subtle' aria-label='更多操作'>
                  <IconDots />
                </ActionIcon>
              </Menu.Target>
              <Menu.Dropdown>
                <Menu.Item onClick={() => setFindOpen(true)}>
                  查找历史
                </Menu.Item>
                <Menu.Item
                  leftSection={<IconRefresh size={16} />}
                  onClick={() => refresh()}
                >
                  刷新对话
                </Menu.Item>
                <Menu.Item onClick={() => stop('all-writes')}>
                  暂停全部自主写入
                </Menu.Item>
                <Menu.Item onClick={() => stop('all-background')}>
                  暂停全部后台工作
                </Menu.Item>
              </Menu.Dropdown>
            </Menu>
          </header>
          {(error || connectionError) && (
            <Alert
              color='orange'
              className='partner-alert'
              title='连接提示'
              withCloseButton
              onClose={() => {
                setError('');
                setConnectionError('');
              }}
            >
              {error || connectionError}
              <Button variant='subtle' size='xs' onClick={() => refresh()}>
                重试连接
              </Button>
            </Alert>
          )}
          <ThreadPrimitive.Root className='partner-thread'>
            <ThreadPrimitive.Viewport
              className='partner-viewport'
              ref={viewport}
            >
              {page?.has_more && (
                <Button
                  className='partner-earlier'
                  variant='subtle'
                  loading={olderLoading}
                  onClick={async () => {
                    if (!page.next_before) return;
                    const height = viewport.current?.scrollHeight || 0;
                    const top = viewport.current?.scrollTop || 0;
                    setOlderLoading(true);
                    await refresh(page.next_before);
                    setOlderLoading(false);
                    requestAnimationFrame(() =>
                      requestAnimationFrame(() => {
                        if (viewport.current)
                          viewport.current.scrollTop =
                            top + viewport.current.scrollHeight - height;
                      })
                    );
                  }}
                >
                  加载更早的消息
                </Button>
              )}
              {loading && !messages.length ? (
                <div className='partner-empty'>
                  <Loader size='sm' />
                  <Text c='dimmed'>正在恢复对话</Text>
                </div>
              ) : (
                <ThreadPrimitive.Empty>
                  <div className='partner-empty'>
                    <Text size='xl' fw={500}>
                      今天有什么要一起推进？
                    </Text>
                    <Text c='dimmed' size='sm'>
                      直接交办，也可以附上图片和资料。
                    </Text>
                  </div>
                </ThreadPrimitive.Empty>
              )}
              <ThreadPrimitive.Messages components={{ Message: ChatMessage }} />
              {(page?.pending || [])
                .filter(
                  (pending) =>
                    !messages.some(
                      (message) => message.request_id === pending.request_id
                    )
                )
                .map((pending) => (
                  <div className='partner-pending' key={pending.request_id}>
                    <Text>{pending.text || '附件消息'}</Text>
                    <SubmittedFiles
                      ids={(pending.attachments || []).map((file) => file.id)}
                    />
                    <Text size='xs' c='dimmed'>
                      {pending.status === 'failed'
                        ? pending.last_error || '处理未完成，可重试本次交办'
                        : '已接收，等待后台处理'}
                    </Text>
                    {pending.status === 'failed' && (
                      <Button
                        size='xs'
                        variant='light'
                        onClick={() =>
                          submit(
                            {
                              client_request_id: pending.request_id,
                              text: pending.text,
                              attachments: (pending.attachments || []).map(
                                (file) => file.id
                              ),
                              references: (pending.references || []).map(
                                ({ object_type, object_id }) => ({
                                  object_type,
                                  object_id
                                })
                              )
                            },
                            true
                          )
                        }
                      >
                        重试本次发送
                      </Button>
                    )}
                  </div>
                ))}
              {submissions.map(({ payload, status, error: failure }) => (
                <div
                  className='partner-pending'
                  key={payload.client_request_id}
                >
                  <Text>{payload.text || '附件消息'}</Text>
                  <SubmittedFiles ids={payload.attachments} />
                  <Text size='xs' c={status === 'failed' ? 'red' : 'dimmed'}>
                    {status === 'sending'
                      ? '正在发送…'
                      : status === 'queued'
                        ? '已接收，等待后台处理'
                        : failure}
                  </Text>
                  {status === 'failed' && (
                    <Button
                      size='xs'
                      variant='light'
                      onClick={() => submit(payload, true)}
                    >
                      重试本次发送
                    </Button>
                  )}
                </div>
              ))}
              {running && (
                <Text
                  className='partner-working'
                  size='sm'
                  c='dimmed'
                  component='output'
                >
                  <Loader size={12} />
                  正在查询和处理，结果会保留在这里。
                </Text>
              )}
            </ThreadPrimitive.Viewport>
            <ThreadPrimitive.ScrollToBottom
              className='partner-scroll-bottom'
              aria-label='滚动到最新消息'
            >
              <IconArrowDown size={18} />
            </ThreadPrimitive.ScrollToBottom>
            <div className='partner-composer-wrap'>
              <ComposerPrimitive.AttachmentDropzone className='partner-dropzone'>
                <ComposerPrimitive.Root className='partner-composer'>
                  <Draft draftKey={draftKey} restoredFiles={restoredFiles} />
                  {!!references.length && (
                    <Group gap={5}>
                      {references.map((reference) => (
                        <Badge
                          key={`${reference.object_type}:${reference.object_id}`}
                          variant='light'
                          rightSection={
                            <ActionIcon
                              size={14}
                              variant='transparent'
                              aria-label={`移除引用 ${reference.label || reference.object_id}`}
                              onClick={() =>
                                setReferences((current) =>
                                  current.filter((item) => item !== reference)
                                )
                              }
                            >
                              <IconX size={12} />
                            </ActionIcon>
                          }
                        >
                          {reference.label ||
                            `${reference.object_type} #${reference.object_id}`}
                        </Badge>
                      ))}
                    </Group>
                  )}
                  <div className='partner-files'>
                    <ComposerPrimitive.Attachments
                      components={{ Attachment: ComposerFile }}
                    />
                  </div>
                  <ComposerPrimitive.Input
                    className='partner-input'
                    placeholder='交办工作，或补充图片和资料…'
                    aria-label='消息内容'
                    rows={2}
                    autoFocus={false}
                    unstable_focusOnRunStart={false}
                    unstable_focusOnScrollToBottom={false}
                    unstable_focusOnThreadSwitched={false}
                  />
                  <Group justify='space-between'>
                    <Group gap='xs'>
                      <ComposerPrimitive.AddAttachment asChild>
                        <ActionIcon
                          variant='subtle'
                          size='lg'
                          aria-label='添加图片或附件'
                        >
                          <IconPaperclip size={21} />
                        </ActionIcon>
                      </ComposerPrimitive.AddAttachment>
                      <Text size='xs' c='dimmed' className='partner-input-hint'>
                        支持粘贴、拖放 · Enter 发送，Shift + Enter 换行
                      </Text>
                    </Group>
                    <Group gap='xs'>
                      {running && (
                        <Button
                          variant='light'
                          color='gray'
                          size='xs'
                          leftSection={<IconPlayerStop size={14} />}
                          onClick={() => stop('reply')}
                        >
                          停止回复
                        </Button>
                      )}
                      <ComposerPrimitive.Send asChild>
                        <ActionIcon
                          variant='filled'
                          radius='xl'
                          size='lg'
                          aria-label='发送消息'
                        >
                          <IconArrowUp size={20} />
                        </ActionIcon>
                      </ComposerPrimitive.Send>
                    </Group>
                  </Group>
                </ComposerPrimitive.Root>
              </ComposerPrimitive.AttachmentDropzone>
              <Text size='xs' c='dimmed' ta='center' mt={6}>
                业务数据以系统记录为准；检验、签字和审批仍按原流程办理。
              </Text>
            </div>
          </ThreadPrimitive.Root>
        </main>
      </AssistantRuntimeProvider>
    </FilesContext.Provider>
  );
}
