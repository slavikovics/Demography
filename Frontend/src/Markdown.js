import { memo, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const copyText = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (e) {
    return false;
  }
};

function CodeBlock({ language, code, t }) {
  const [copied, setCopied] = useState(false);

  const onCopy = async () => {
    if (await copyText(code)) {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }
  };

  return (
    <div className="md-code">
      <div className="md-code__bar">
        <span>{language || 'text'}</span>
        <button type="button" className="md-code__copy" onClick={onCopy}>{copied ? t('chat.copied') : t('chat.copy')}</button>
      </div>
      <pre><code>{code}</code></pre>
    </div>
  );
}

const textOf = (node) => (Array.isArray(node) ? node.map(textOf).join('') : typeof node === 'string' ? node : '');

/**
 * Безопасный markdown (GFM: таблицы, списки, зачёркивание, задачи). Сырой HTML не рендерится.
 * Стилизация — в Chat.css (.md).
 */
function Markdown({ text, t }) {
  const components = {
    a: ({ node, children, ...props }) => <a {...props} target="_blank" rel="noopener noreferrer">{children}</a>,
    table: ({ node, ...props }) => (
      <div className="md-table-wrap" tabIndex={0}>
        <table {...props} />
      </div>
    ),
    pre: ({ children }) => <>{children}</>,
    code: ({ node, className, children, ...props }) => {
      const language = /language-(\w+)/.exec(className || '')?.[1];
      const code = textOf(children).replace(/\n$/, '');
      const isBlock = Boolean(language) || code.includes('\n');
      return isBlock
        ? <CodeBlock language={language} code={code} t={t} />
        : <code className="md-inline-code" {...props}>{children}</code>;
    },
  };

  return (
    <div className="md">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components} disallowedElements={['img']} unwrapDisallowed>
        {text}
      </ReactMarkdown>
    </div>
  );
}

export default memo(Markdown);
export { copyText };
