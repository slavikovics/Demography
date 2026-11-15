import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import ChatMessage from './ChatMessage';
import { collectTerritoryNames } from './ToolCallCard';
import { MAX_MESSAGE_CHARS } from './useChat';
import { apiUrl } from './config';
import { useFetchJson } from './hooks';
import './Chat.css';

const SUGGESTIONS = [1, 2, 3, 4, 5, 6];
const BOTTOM_THRESHOLD_PX = 80;

function EmptyState({ t, onPick }) {
  return (
    <div className="chat-empty">
      <span className="chat-empty__mark" aria-hidden="true">
        <svg width="30" height="30" viewBox="0 0 20 20" focusable="false">
          <path d="M4 5.5A2.5 2.5 0 016.5 3h7A2.5 2.5 0 0116 5.5v5A2.5 2.5 0 0113.5 13H9l-3.5 3v-3A2.5 2.5 0 014 10.5v-5z" fill="#fff" />
        </svg>
      </span>
      <h2 className="chat-empty__title">{t('chat.empty.title')}</h2>
      <p className="chat-empty__subtitle">{t('chat.empty.subtitle')}</p>
      <div className="chat-empty__label">{t('chat.suggestions')}</div>
      <div className="chat-empty__chips">
        {SUGGESTIONS.map((n) => (
          <button key={n} type="button" className="suggestion" onClick={() => onPick(t(`chat.suggestion.${n}`))}>
            {t(`chat.suggestion.${n}`)}
          </button>
        ))}
      </div>
    </div>
  );
}

function ChatPage({ t, language, indicators, chat }) {
  const { messages, streaming, send, stop, retry, clear } = chat;
  const [input, setInput] = useState('');
  const [confirmClear, setConfirmClear] = useState(false);
  const [atBottom, setAtBottom] = useState(true);

  const listRef = useRef(null);
  const inputRef = useRef(null);
  const stickRef = useRef(true);

  const health = useFetchJson(`${apiUrl}/chat/health`);
  const territoryNames = useMemo(() => collectTerritoryNames(messages), [messages]);

  // после каждого ответа заново проверяем доступность чата: баннер не должен «залипать»
  const { reload: reloadHealth } = health;
  useEffect(() => { if (!streaming) reloadHealth(); }, [streaming, reloadHealth]);

  // ---- прокрутка: следуем за ответом, пока пользователь сам не прокрутил вверх
  const scrollToBottom = useCallback((smooth = false) => {
    const el = listRef.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: smooth ? 'smooth' : 'auto' });
  }, []);

  useLayoutEffect(() => {
    if (stickRef.current) scrollToBottom();
  }, [messages, scrollToBottom]);

  const onScroll = () => {
    const el = listRef.current;
    const near = el.scrollHeight - el.scrollTop - el.clientHeight < BOTTOM_THRESHOLD_PX;
    stickRef.current = near;
    setAtBottom(near);
  };

  // ---- поле ввода
  const resizeInput = () => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 168)}px`;
  };

  useEffect(resizeInput, [input]);
  useEffect(() => { if (!streaming) inputRef.current?.focus(); }, [streaming]);
  useEffect(() => { if (!confirmClear) return undefined; const timer = setTimeout(() => setConfirmClear(false), 12000); return () => clearTimeout(timer); }, [confirmClear]);

  const submit = (text = input) => {
    stickRef.current = true;
    if (send(text)) {
      setInput('');
      requestAnimationFrame(() => scrollToBottom());
    }
  };

  const onKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      if (!streaming) submit();
    }
  };

  const overLimit = input.length > MAX_MESSAGE_CHARS;
  const canSend = input.trim().length > 0 && !overLimit && !streaming;

  // ---- недоступность чата (нет ключа / MCP / API)
  let unavailable = null;
  if (health.error) unavailable = t('chat.unavailable.api');
  else if (health.data && !health.data.configured) unavailable = t('chat.unavailable.key');
  else if (health.data && !health.data.mcp?.connected) unavailable = t('chat.unavailable.mcp');


  return (
    <div className="chat-page">
      <header className="chat-bar">
        <div className="chat-bar__heading">
          <h2 className="chat-bar__title">{t('chat.title')}</h2>
          <p className="chat-bar__subtitle">{t('chat.subtitle')}</p>
        </div>

        <div className="chat-bar__actions">
          {confirmClear ? (
            <div className="confirm" role="group" aria-label={t('chat.clearConfirm')}>
              <span>{t('chat.clearConfirm')}</span>
              <button type="button" className="button-danger" onClick={() => { clear(); setConfirmClear(false); }}>{t('chat.clearYes')}</button>
              <button type="button" className="button-secondary" onClick={() => setConfirmClear(false)}>{t('chat.clearNo')}</button>
            </div>
          ) : (
            <button type="button" className="button-secondary" disabled={messages.length === 0} onClick={() => setConfirmClear(true)}>
              <svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true" focusable="false">
                <path d="M3 4.5h10M6.5 4.5V3h3v1.5M5 4.5l.6 8.5h4.8l.6-8.5" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              {t('chat.clear')}
            </button>
          )}
        </div>
      </header>

      {unavailable && (
        <div className="chat-banner" role="alert">
          <div>
            <strong>{t('chat.unavailable')}</strong>
            <span>{unavailable}</span>
          </div>
          <button type="button" className="button-secondary" onClick={health.reload}>{t('common.retry')}</button>
        </div>
      )}

      <div className="chat-scroll" ref={listRef} onScroll={onScroll} role="log" aria-live="polite" aria-label={t('chat.title')}>
        <div className="chat-column">
          {messages.length === 0 ? (
            <EmptyState t={t} onPick={(text) => submit(text)} />
          ) : (
            messages.map((message, index) => (
              <ChatMessage
                key={message.id}
                t={t}
                language={language}
                message={message}
                indicators={indicators}
                territoryNames={territoryNames}
                isLast={index === messages.length - 1}
                busy={streaming}
                onRetry={retry}
              />
            ))
          )}
        </div>
      </div>

      {!atBottom && messages.length > 0 && (
        <button type="button" className="scroll-down" onClick={() => { stickRef.current = true; scrollToBottom(true); }}>
          <svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true" focusable="false">
            <path d="M8 3v9M4 8.5l4 4 4-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          {t('chat.scrollDown')}
        </button>
      )}

      <form className="composer" onSubmit={(event) => { event.preventDefault(); if (canSend) submit(); }}>
        <div className="composer__box">
          <textarea
            ref={inputRef}
            className="composer__input"
            rows={1}
            value={input}
            placeholder={t('chat.placeholder')}
            aria-label={t('chat.placeholder')}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={onKeyDown}
          />
          {streaming ? (
            <button type="button" className="composer__button composer__button--stop" onClick={stop} aria-label={t('chat.stop')} title={t('chat.stop')}>
              <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true" focusable="false"><rect x="3.5" y="3.5" width="9" height="9" rx="1.8" fill="currentColor" /></svg>
            </button>
          ) : (
            <button type="submit" className="composer__button" disabled={!canSend} aria-label={t('chat.send')} title={t('chat.send')}>
              <svg width="18" height="18" viewBox="0 0 20 20" aria-hidden="true" focusable="false">
                <path d="M10 16V4M5 9l5-5 5 5" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          )}
        </div>
        <div className="composer__footer">
          <span>{t('chat.disclaimer')}</span>
          <span className={`composer__counter${overLimit ? ' composer__counter--over' : ''}`}>
            {input.length > MAX_MESSAGE_CHARS * 0.7 ? t('chat.charCount', { count: input.length, max: MAX_MESSAGE_CHARS }) : t('chat.hintKeys')}
          </span>
        </div>
      </form>
    </div>
  );
}

export default ChatPage;
