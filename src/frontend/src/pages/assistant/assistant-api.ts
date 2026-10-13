import type {
  CompleteAttachment,
  ThreadMessageLike
} from '@assistant-ui/react';

export const ASSISTANT_API = '/api/cangxu/assistant/';
export const ATTACHMENT_ACCEPT =
  '.png,.jpg,.jpeg,.webp,.gif,.pdf,.docx,.xlsx,.csv,.tsv,.txt,.md,.json,.log';
export type PartnerSummary = {
  partner_id: string;
  conversation_id: string;
  display_name: string;
  is_default: boolean;
  enabled: boolean;
  write_enabled: boolean;
  created_at: string;
  updated_at: string;
  last_message?: string;
  last_message_at?: string | null;
};
export type PartnerActivity = {
  partner_id: string;
  preview: string;
  last_message_at?: string;
  running: boolean;
};
export type BusinessReference = {
  object_type: string;
  object_id: string;
  label?: string;
  page_url?: string;
};
export type AttachmentInfo = {
  id: string;
  name: string;
  original_name?: string;
  mime_type: string;
  size: number;
  download_url: string;
  preview_url?: string | null;
  available?: boolean;
  extraction_status?: string;
  extraction_note?: string;
};
export type HistoryMessage = {
  id: number | string;
  role: 'user' | 'assistant';
  text: string;
  created_at?: string;
  request_id?: string;
  attachments?: AttachmentInfo[];
  references?: BusinessReference[];
};
export type HistoryPage = {
  items: HistoryMessage[];
  next_before: number | null;
  has_more: boolean;
  reply_running?: boolean;
  is_running?: boolean;
  active_tasks?: { id: number; status: string }[];
  runtime_status?: {
    status: string;
    is_running: boolean;
    reply_running: boolean;
    live_message?: HistoryMessage | null;
    live_tools?: { name: string; status: string }[];
    active_tasks?: { id: number; status: string }[];
  };
  pending?: {
    request_id: string;
    text: string;
    status: string;
    last_error?: string;
    attachments?: AttachmentInfo[];
    references?: BusinessReference[];
  }[];
};
export type Submission = {
  client_request_id: string;
  text: string;
  attachments: string[];
  references: { object_type: string; object_id: string }[];
};

export function attachmentName(file: AttachmentInfo) {
  return file.name || file.original_name || '附件';
}
export function toAttachment(file: AttachmentInfo): CompleteAttachment {
  return {
    id: file.id,
    name: attachmentName(file),
    type: file.mime_type.startsWith('image/') ? 'image' : 'document',
    contentType: file.mime_type,
    status: { type: 'complete' },
    content: []
  };
}
export function toMessage(message: HistoryMessage): ThreadMessageLike {
  return {
    id: String(message.id),
    role: message.role,
    content: message.text || '',
    createdAt: message.created_at ? new Date(message.created_at) : undefined,
    attachments: (message.attachments || []).map(toAttachment),
    metadata: { custom: { references: message.references || [] } }
  };
}
export function apiError(error: unknown): string {
  const response = (error as { response?: { status?: number; data?: unknown } })
    ?.response;
  if (!response) return '网络连接中断，请重试。已接收的工作会继续运行。';
  if (response.status === 401) return '登录已过期，请重新登录后继续。';
  if (response.status === 403) return '当前账号没有执行此操作的业务权限。';
  if (response.status === 413) return '文件过大，请缩小文件后重试。';
  if (response.status === 503)
    return '工作伙伴暂时无法连接；原业务页面仍可使用。';
  const value = response.data;
  if (typeof value === 'object' && value !== null)
    return Object.values(value).flat().map(String).join('；').slice(0, 500);
  return '请求未完成，请重试。';
}
