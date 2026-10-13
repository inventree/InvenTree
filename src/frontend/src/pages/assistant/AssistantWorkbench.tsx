import {
  ActionIcon,
  Alert,
  Button,
  Menu,
  Modal,
  TextInput,
  Tooltip
} from '@mantine/core';
import {
  IconArrowLeft,
  IconChevronRight,
  IconDeviceDesktop,
  IconPlus,
  IconSearch,
  IconSettings
} from '@tabler/icons-react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import { useApi } from '../../contexts/ApiContext';
import { useUserState } from '../../states/UserState';
import AssistantPage from './AssistantPage';
import PartnerAvatar from './PartnerAvatar';
import {
  ASSISTANT_API,
  type PartnerActivity,
  type PartnerSummary,
  apiError
} from './assistant-api';
import './assistant.css';

function recentTime(value?: string | null) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toDateString() === new Date().toDateString()
    ? date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    : date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' });
}
export default function AssistantWorkbench() {
  const api = useApi();
  const location = useLocation();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const user = useUserState((state) => state.user);
  const storageKey = `cangxu-assistant-selected:${api.defaults.baseURL || window.location.origin}:${user?.pk}`;
  const loadSequence = useRef(0);
  const [partners, setPartners] = useState<PartnerSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activity, setActivity] = useState<Record<string, PartnerActivity>>(
    () => {
      try {
        return JSON.parse(
          sessionStorage.getItem(`${storageKey}:activity`) || '{}'
        );
      } catch {
        return {};
      }
    }
  );
  useEffect(() => {
    try {
      sessionStorage.setItem(
        `${storageKey}:activity`,
        JSON.stringify(
          Object.fromEntries(
            Object.entries(activity)
              .slice(-128)
              .map(([id, item]) => [
                id,
                { ...item, preview: item.preview.slice(0, 200), running: false }
              ])
          )
        )
      );
    } catch {
      /* Storage limits must not interrupt a live conversation. */
    }
  }, [activity, storageKey]);
  const [editing, setEditing] = useState<'create' | 'rename' | null>(null);
  const [name, setName] = useState('');
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');
  const selectedId = searchParams.get('partner');
  const selected = partners.find((item) => item.partner_id === selectedId);
  const load = useCallback(async () => {
    const sequence = ++loadSequence.current;
    try {
      const { data } = await api.get<{ results: PartnerSummary[] }>(
        `${ASSISTANT_API}partners/`,
        { timeout: 15000 }
      );
      if (sequence !== loadSequence.current) return;
      setPartners(data.results);
      setError('');
    } catch (error) {
      if (sequence === loadSequence.current) setError(apiError(error));
    } finally {
      if (sequence === loadSequence.current) setLoading(false);
    }
  }, [api]);
  useEffect(() => {
    void load();
    const timer = setInterval(() => {
      if (!document.hidden) void load();
    }, 15000);
    return () => {
      clearInterval(timer);
      loadSequence.current++;
    };
  }, [load]);
  useEffect(() => {
    if (!partners.length) return;
    if (selected) {
      sessionStorage.setItem(storageKey, selected.partner_id);
      return;
    }
    const previous = sessionStorage.getItem(storageKey);
    const target =
      (!location.state?.references?.length &&
        partners.find((item) => item.partner_id === previous)) ||
      partners.find((item) => item.is_default) ||
      partners[0];
    setSearchParams(
      (params) => {
        params.set('partner', target.partner_id);
        return params;
      },
      { replace: true, state: location.state }
    );
  }, [partners, selected, storageKey, setSearchParams, location.state]);
  const onActivity = useCallback((next: PartnerActivity) => {
    setActivity((current) => ({
      ...current,
      [next.partner_id]: {
        ...next,
        preview: next.preview
          .replace(/\*\*|__|`|^#{1,6} /g, '')
          .replace(/\s+/g, ' ')
          .trim()
          .slice(0, 200)
      }
    }));
  }, []);
  const visible = useMemo(
    () =>
      partners.filter((partner) =>
        `${partner.display_name} ${activity[partner.partner_id]?.preview || partner.last_message || ''}`
          .toLocaleLowerCase()
          .includes(search.toLocaleLowerCase())
      ),
    [partners, search, activity]
  );
  function select(partner: PartnerSummary) {
    setSearchParams(
      (params) => {
        params.set('partner', partner.partner_id);
        return params;
      },
      { state: location.state }
    );
    setSidebarOpen(false);
  }
  async function save() {
    if (!name.trim() || saving) return;
    setSaving(true);
    setFormError('');
    try {
      const { data } =
        editing === 'rename' && selected
          ? await api.patch<PartnerSummary>(
              `${ASSISTANT_API}partners/${selected.partner_id}/`,
              { display_name: name.trim() }
            )
          : await api.post<PartnerSummary>(`${ASSISTANT_API}partners/`, {
              display_name: name.trim()
            });
      setPartners((current) =>
        current.some((item) => item.partner_id === data.partner_id)
          ? current.map((item) =>
              item.partner_id === data.partner_id ? data : item
            )
          : [...current, data]
      );
      select(data);
      setEditing(null);
      void load();
    } catch (error) {
      setFormError(apiError(error));
    } finally {
      setSaving(false);
    }
  }
  const username =
    [user?.first_name, user?.last_name].filter(Boolean).join(' ') ||
    user?.username ||
    '我的账号';
  return (
    <div className='partner-workbench-backdrop'>
      <div className='partner-workbench' data-sidebar-open={sidebarOpen}>
        <aside className='partner-sidebar' aria-label='伙伴列表'>
          <div className='partner-sidebar-top'>
            <button
              type='button'
              className='partner-brand'
              onClick={() => navigate('/cangxu/')}
              aria-label='返回仓序业务工作台'
            >
              <span />
              仓序
            </button>
            <Tooltip label='新建伙伴'>
              <ActionIcon
                variant='subtle'
                size='lg'
                aria-label='新建伙伴'
                onClick={() => {
                  setName('');
                  setFormError('');
                  setEditing('create');
                }}
              >
                <IconPlus size={23} />
              </ActionIcon>
            </Tooltip>
          </div>
          <div className='partner-search'>
            <IconSearch size={22} />
            <input
              aria-label='搜索伙伴'
              placeholder='搜索'
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>
          <nav className='partner-list' aria-label='常驻伙伴'>
            {visible.map((partner) => {
              const latest = activity[partner.partner_id];
              const active = selectedId === partner.partner_id;
              const running = active && latest?.running;
              return (
                <button
                  type='button'
                  className={`partner-list-item${active ? ' is-selected' : ''}`}
                  key={partner.partner_id}
                  onClick={() => select(partner)}
                  aria-current={active ? 'page' : undefined}
                  aria-label={`打开伙伴 ${partner.display_name}`}
                >
                  <PartnerAvatar id={partner.partner_id} size={48} />
                  <span className='partner-list-copy'>
                    <span className='partner-list-line'>
                      <span className='partner-list-name'>
                        {partner.display_name}
                      </span>
                      <time>
                        {recentTime(
                          latest?.last_message_at || partner.last_message_at
                        )}
                      </time>
                    </span>
                    <span
                      className={`partner-list-preview${running ? ' is-running' : ''}`}
                    >
                      {!partner.enabled
                        ? '伙伴已暂停'
                        : running
                          ? '正在处理…'
                          : latest?.preview ||
                            partner.last_message ||
                            '开始交办工作'}
                    </span>
                  </span>
                </button>
              );
            })}
            {loading && (
              <output className='partner-list-notice'>正在连接伙伴…</output>
            )}
            {!loading && !error && !visible.length && (
              <p className='partner-list-notice'>
                {search ? '没有找到伙伴' : '还没有伙伴'}
              </p>
            )}
            {error && (
              <div className='partner-list-notice' role='alert'>
                {error}
                <Button variant='subtle' size='xs' onClick={() => load()}>
                  重试连接
                </Button>
              </div>
            )}
          </nav>
          <Menu position='top-start'>
            <Menu.Target>
              <button
                type='button'
                className='partner-account'
                aria-label='账号菜单'
              >
                <span className='partner-account-avatar'>
                  {username.slice(0, 2).toUpperCase()}
                </span>
                <span>{username}</span>
                <IconChevronRight size={18} />
              </button>
            </Menu.Target>
            <Menu.Dropdown className='partner-menu'>
              <Menu.Item
                leftSection={<IconSettings size={16} />}
                onClick={() => navigate('/settings/user/')}
              >
                个人设置
              </Menu.Item>
              <Menu.Item
                leftSection={<IconDeviceDesktop size={16} />}
                onClick={() => navigate('/cangxu/')}
              >
                返回业务页面
              </Menu.Item>
            </Menu.Dropdown>
          </Menu>
        </aside>
        <section className='partner-conversation' aria-label='当前伙伴'>
          {selected ? (
            <AssistantPage
              key={selected.partner_id}
              partner={selected}
              onOpenList={() => setSidebarOpen(true)}
              onRename={() => {
                setName(selected.display_name);
                setFormError('');
                setEditing('rename');
              }}
              onActivity={onActivity}
              inheritReferences={selected.is_default}
            />
          ) : (
            <div className='partner-select-empty'>
              <button
                className='partner-mobile-back'
                type='button'
                onClick={() => setSidebarOpen(true)}
              >
                <IconArrowLeft size={20} />
                伙伴列表
              </button>
              <PartnerAvatar id='default' size={56} />
              <p>
                {loading
                  ? '正在连接伙伴…'
                  : error
                    ? '连接暂时中断'
                    : '选择一个伙伴，继续交办工作'}
              </p>
              {error && (
                <Button variant='subtle' onClick={() => load()}>
                  重试连接
                </Button>
              )}
            </div>
          )}
        </section>
        <Modal
          className='partner-dialog'
          opened={editing !== null}
          onClose={() => setEditing(null)}
          title={editing === 'rename' ? '重命名伙伴' : '新建伙伴'}
          centered
        >
          <form
            onSubmit={(event) => {
              event.preventDefault();
              void save();
            }}
          >
            {formError && (
              <Alert color='orange' mb='sm'>
                {formError}
              </Alert>
            )}
            <TextInput
              label='伙伴名称'
              placeholder='例如：库存伙伴'
              value={name}
              onChange={(event) => setName(event.target.value)}
              maxLength={80}
              required
              data-autofocus
            />
            <Button
              type='submit'
              mt='md'
              fullWidth
              loading={saving}
              disabled={!name.trim()}
            >
              {editing === 'rename' ? '保存名称' : '创建伙伴'}
            </Button>
          </form>
        </Modal>
      </div>
    </div>
  );
}
