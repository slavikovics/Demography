import { memo, useState } from 'react';
import Markdown, { copyText } from './Markdown';
import ToolCallCard from './ToolCallCard';
import { textOf } from './useChat';

function Avatar() {
  return (
    <span className="avatar" aria-hidden="true">
      <svg width="18" height="18" viewBox="0 0 20 20" focusable="false">
        <path d="M4 5.5A2.5 2.5 0 016.5 3h7A2.5 2.5 0 0116 5.5v5A2.5 2.5 0 0113.5 13H9l-3.5 3v-3A2.5 2.5 0 014 10.5v-5z" fill="#fff" />
      </svg>
    </span>
  );
}

function ReasoningBlock({ t, text, live }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={`reasoning${live ? ' reasoning--live' : ''}`}>
      <button type="button" className="reasoning__toggle" aria-expanded={open} onClick={() => setOpen((v) => !v)}>
        <svg width="16" height="16" viewBox="0 0 20 20" aria-hidden="true" focusable="false">
          <path d="M10 3a5 5 0 00-3 9v2h6v-2a5 5 0 00-3-9zM8 17h4" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <span>{live ? t('chat.reasoningLive') : t('chat.reasoning')}</span>
        <svg className={`reasoning__chevron${open ? ' reasoning__chevron--open' : ''}`} width="12" height="12" viewBox="0 0 16 16" aria-hidden="true" focusable="false">
          <path d="M3.5 6l4.5 4.5L12.5 6" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
      {open && <div className="reasoning__text">{text}</div>}
    </div>
  );
}

function TypingDots({ label }) {
  return (
    <div className="typing" role="status" aria-label={label}>
      <span /><span /><span />
      <em>{label}</em>
    </div>
  );
}

const shortModel = (model) => (model || '').replace(/^~?[^/]+\//, '');

function ChatMessage({ t, language, message, indicators, territoryNames, isLast, busy, onRetry }) {
  const [copied, setCopied] = useState(false);

  if (message.role === 'user') {
    return (
      <div className="msg msg--user">
        <div className="msg__bubble">{message.content}</div>
      </div>
    );
  }

  const parts = message.parts || [];
  const streaming = message.status === 'streaming';
  const lastPart = parts[parts.length - 1];
  const waiting = streaming && (!lastPart || (lastPart.type === 'tool' && lastPart.status !== 'running'));
  const answer = textOf(message);
  const { meta } = message;

  const onCopy = async () => {
    if (await copyText(answer)) {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }
  };

  return (
    <div className="msg msg--assistant">
      <Avatar />
      <div className="msg__body">
        {parts.map((part, index) => {
          if (part.type === 'reasoning') {
            return <ReasoningBlock key={index} t={t} text={part.text} live={streaming && index === parts.length - 1} />;
          }
          if (part.type === 'tool') {
            return <ToolCallCard key={part.id} t={t} language={language} part={part} indicators={indicators} territoryNames={territoryNames} />;
          }
          const isTail = streaming && index === parts.length - 1;
          return (
            <div className="msg__text" key={index}>
              <Markdown text={part.text} t={t} />
              {isTail && <span className="cursor" aria-hidden="true" />}
            </div>
          );
        })}

        {waiting && <TypingDots label={t('chat.thinking')} />}

        {message.status === 'error' && (
          <div className="msg__error" role="alert">
            <span>{message.error?.message || t('chat.error.network')}</span>
            {isLast && !busy && <button type="button" className="button-secondary" onClick={onRetry}>{t('chat.retry')}</button>}
          </div>
        )}
        {message.status === 'stopped' && <div className="msg__stopped">{t('chat.stopped')}</div>}

        {!streaming && (answer || meta?.model) && (
          <div className="msg__footer">
            <span className="msg__meta">
              {meta?.model && <span title={meta.model}>{shortModel(meta.model)}</span>}
              {meta?.usage?.total_tokens ? <span>{t('chat.meta.tokens', { n: meta.usage.total_tokens.toLocaleString(language === 'english' ? 'en-US' : 'ru-RU') })}</span> : null}
              {meta?.durationMs ? <span>{t('chat.meta.seconds', { n: (meta.durationMs / 1000).toFixed(1) })}</span> : null}
              {meta?.iterations > 1 ? <span>{t('chat.meta.steps', { n: meta.iterations })}</span> : null}
            </span>
            <span className="msg__actions">
              {answer && <button type="button" className="link-button" onClick={onCopy}>{copied ? t('chat.copied') : t('chat.copy')}</button>}
              {isLast && !busy && message.status !== 'error' && <button type="button" className="link-button" onClick={onRetry}>{t('chat.regenerate')}</button>}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

export default memo(ChatMessage);
