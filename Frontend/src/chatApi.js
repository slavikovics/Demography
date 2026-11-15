import { apiUrl } from './config';

export class ChatHttpError extends Error {
  constructor(status, detail) {
    super(detail || `HTTP ${status}`);
    this.name = 'ChatHttpError';
    this.status = status;
  }
}

// Разбор одного SSE-блока: «event: name\ndata: {json}». Комментарии (": keep-alive") пропускаются.
function parseBlock(block) {
  let event = 'message';
  const data = [];
  block.split('\n').forEach((line) => {
    if (!line || line.startsWith(':')) return;
    if (line.startsWith('event:')) event = line.slice(6).trim();
    else if (line.startsWith('data:')) data.push(line.slice(5).replace(/^ /, ''));
  });
  if (data.length === 0) return null;
  try {
    return { event, data: JSON.parse(data.join('\n')) };
  } catch (e) {
    return null;
  }
}

/**
 * Отправляет историю на бэкенд и вызывает onEvent({event, data}) по мере поступления SSE-событий.
 * Поток читается через fetch (EventSource не умеет POST). Отмена — через AbortSignal.
 */
export async function streamChat({ messages, language, signal, onEvent }) {
  const response = await fetch(`${apiUrl}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify({ messages, language }),
    signal,
  });

  if (!response.ok) {
    let detail = '';
    try {
      const body = await response.json();
      detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
    } catch (e) {
      // тело не JSON — достаточно статуса
    }
    throw new ChatHttpError(response.status, detail);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    // чанки могут резать событие в любом месте — копим буфер до пустой строки
    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n');
    let boundary;
    while ((boundary = buffer.indexOf('\n\n')) !== -1) {
      const parsed = parseBlock(buffer.slice(0, boundary));
      buffer = buffer.slice(boundary + 2);
      if (parsed) onEvent(parsed);
    }
  }

  const rest = parseBlock(buffer + decoder.decode());
  if (rest) onEvent(rest);
}
