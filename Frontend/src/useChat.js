import { useCallback, useEffect, useRef, useState } from 'react';
import { ChatHttpError, streamChat } from './chatApi';

const STORAGE_KEY = 'demography.chat.v1';
const MAX_STORED_MESSAGES = 100;
const STORED_PREVIEW_CHARS = 1500;
const STORED_REASONING_CHARS = 6000;
const HISTORY_LIMIT = 20;

export const MAX_MESSAGE_CHARS = 2000;

const uid = () => (window.crypto?.randomUUID ? window.crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}`);

// Прерванные вызовы инструментов помечаются, чтобы в истории не оставалось «вечных» спиннеров
const settleParts = (parts) => parts.map((part) => (
  part.type === 'tool' && part.status === 'running' ? { ...part, status: 'cancelled' } : part
));

function loadMessages() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    const data = raw ? JSON.parse(raw) : [];
    if (!Array.isArray(data)) return [];
    // вкладку могли закрыть посреди ответа
    return data.map((m) => (m.status === 'streaming' ? { ...m, status: 'stopped', parts: settleParts(m.parts || []) } : m));
  } catch (e) {
    return [];
  }
}

// В хранилище кладём урезанную копию: полные результаты инструментов могут быть большими
function compact(messages) {
  return messages.map((m) => (m.role !== 'assistant' ? m : {
    ...m,
    parts: (m.parts || []).map((part) => {
      if (part.type === 'tool') return { ...part, preview: (part.preview || '').slice(0, STORED_PREVIEW_CHARS), truncated: part.truncated || (part.preview || '').length > STORED_PREVIEW_CHARS };
      if (part.type === 'reasoning') return { ...part, text: part.text.slice(0, STORED_REASONING_CHARS) };
      return part;
    }),
  }));
}

function saveMessages(messages) {
  let list = compact(messages).slice(-MAX_STORED_MESSAGES);
  while (list.length > 0) {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
      return;
    } catch (e) {
      list = list.slice(Math.ceil(list.length / 4));   // квота исчерпана — выбрасываем самые старые
    }
  }
  try { window.localStorage.removeItem(STORAGE_KEY); } catch (e) { /* хранилище недоступно */ }
}

export const textOf = (message) => (message.role === 'user'
  ? message.content
  : (message.parts || []).filter((p) => p.type === 'text').map((p) => p.text).join('').trim());

function toPayload(history) {
  return history
    .map((m) => ({ role: m.role, content: textOf(m) }))
    .filter((m) => m.content)
    .slice(-HISTORY_LIMIT);
}

const appendText = (message, type, text) => {
  const parts = [...message.parts];
  const last = parts[parts.length - 1];
  if (last && last.type === type) parts[parts.length - 1] = { ...last, text: last.text + text };
  else parts.push({ type, text });
  return { ...message, parts };
};

export function useChat({ language, t }) {
  const [messages, setMessages] = useState(loadMessages);
  const [streaming, setStreaming] = useState(false);
  const controllerRef = useRef(null);
  const messagesRef = useRef(messages);
  messagesRef.current = messages;

  // ---- сохранение истории (с задержкой, чтобы не писать в localStorage на каждый токен)
  useEffect(() => {
    const timer = setTimeout(() => saveMessages(messages), streaming ? 1500 : 250);
    return () => clearTimeout(timer);
  }, [messages, streaming]);

  useEffect(() => {
    const flush = () => saveMessages(messagesRef.current);
    window.addEventListener('beforeunload', flush);
    return () => { window.removeEventListener('beforeunload', flush); flush(); };
  }, []);

  // ---- пакетное применение дельт: не чаще одного обновления состояния на кадр
  const queueRef = useRef({ id: null, ops: [], frame: 0 });

  const flushQueue = useCallback(() => {
    const queue = queueRef.current;
    if (queue.frame) { cancelAnimationFrame(queue.frame); queue.frame = 0; }
    const { id, ops } = queue;
    queue.ops = [];
    if (!id || ops.length === 0) return;
    setMessages((list) => list.map((m) => (m.id === id ? ops.reduce((acc, op) => op(acc), m) : m)));
  }, []);

  const enqueue = useCallback((id, op) => {
    const queue = queueRef.current;
    queue.id = id;
    queue.ops.push(op);
    if (!queue.frame) queue.frame = requestAnimationFrame(flushQueue);
  }, [flushQueue]);

  const patch = useCallback((id, fn) => {
    flushQueue();   // сначала накопленные дельты — порядок событий сохраняется
    setMessages((list) => list.map((m) => (m.id === id ? fn(m) : m)));
  }, [flushQueue]);

  const handleEvent = useCallback((id, { event, data }) => {
    switch (event) {
      case 'run_start':
        patch(id, (m) => ({ ...m, meta: { ...m.meta, model: data.model } }));
        break;
      case 'reasoning_delta':
        enqueue(id, (m) => appendText(m, 'reasoning', data.text));
        break;
      case 'token':
        enqueue(id, (m) => appendText(m, 'text', data.text));
        break;
      case 'tool_call':
        patch(id, (m) => ({ ...m, parts: [...m.parts, { type: 'tool', id: data.id, name: data.name, arguments: data.arguments, status: 'running' }] }));
        break;
      case 'tool_result':
        patch(id, (m) => ({
          ...m,
          parts: m.parts.map((p) => (p.type === 'tool' && p.id === data.id ? {
            ...p, status: data.ok ? 'ok' : 'error', durationMs: data.duration_ms, counts: data.counts,
            preview: data.preview, truncated: data.truncated,
          } : p)),
        }));
        break;
      case 'done':
        patch(id, (m) => ({
          ...m, status: 'done',
          meta: { model: data.model, usage: data.usage, cost: data.cost, durationMs: data.duration_ms, iterations: data.iterations },
        }));
        break;
      case 'error': {
        // известные коды локализуем на клиенте, остальные показываем как пришли
        const key = `chat.error.code.${data.code}`;
        const localized = t(key);
        patch(id, (m) => ({ ...m, status: 'error', error: { code: data.code, message: localized !== key ? localized : data.message } }));
        break;
      }
      default:
        break;
    }
  }, [enqueue, patch, t]);

  const run = useCallback(async (history, assistantId) => {
    const controller = new AbortController();
    controllerRef.current = controller;
    setStreaming(true);

    try {
      await streamChat({
        messages: toPayload(history), language, signal: controller.signal,
        onEvent: (evt) => handleEvent(assistantId, evt),
      });
      flushQueue();
      // поток закончился без события done/error
      patch(assistantId, (m) => (m.status !== 'streaming' ? m : (
        textOf(m) ? { ...m, status: 'done' } : { ...m, status: 'error', error: { code: 'empty', message: t('chat.error.empty') } }
      )));
    } catch (e) {
      flushQueue();
      if (e.name === 'AbortError') {
        patch(assistantId, (m) => ({ ...m, status: 'stopped' }));
      } else {
        const message = e instanceof ChatHttpError
          ? (e.status === 429 ? t('chat.error.rateLimit') : e.status === 503 ? t('chat.error.unavailable') : e.message)
          : t('chat.error.network');
        patch(assistantId, (m) => ({ ...m, status: 'error', error: { code: e.status || 'network', message } }));
      }
    } finally {
      flushQueue();
      patch(assistantId, (m) => ({ ...m, parts: settleParts(m.parts) }));
      controllerRef.current = null;
      setStreaming(false);
    }
  }, [flushQueue, handleEvent, language, patch, t]);

  const start = useCallback((history) => {
    const assistant = { id: uid(), role: 'assistant', parts: [], status: 'streaming', createdAt: Date.now(), meta: {} };
    setMessages([...history, assistant]);
    run(history, assistant.id);
  }, [run]);

  const send = useCallback((text) => {
    const content = text.trim();
    if (!content || controllerRef.current) return false;
    start([...messagesRef.current, { id: uid(), role: 'user', content, createdAt: Date.now() }]);
    return true;
  }, [start]);

  const stop = useCallback(() => controllerRef.current?.abort(), []);

  // Повторить последний вопрос: ответ(ы) после него отбрасываются
  const retry = useCallback(() => {
    if (controllerRef.current) return;
    const list = messagesRef.current;
    const lastUser = list.map((m) => m.role).lastIndexOf('user');
    if (lastUser < 0) return;
    start(list.slice(0, lastUser + 1));
  }, [start]);

  const clear = useCallback(() => {
    controllerRef.current?.abort();
    queueRef.current.ops = [];
    setMessages([]);
    try { window.localStorage.removeItem(STORAGE_KEY); } catch (e) { /* ignore */ }
  }, []);

  useEffect(() => () => controllerRef.current?.abort(), []);

  return { messages, streaming, send, stop, retry, clear };
}
