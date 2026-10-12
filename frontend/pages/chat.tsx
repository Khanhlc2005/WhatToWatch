import Head from 'next/head';
import Link from 'next/link';
import { FormEvent, useCallback, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '../components/Layout';
import { ChatMessage, ChatReply, Conversation, ConversationDetail } from '../lib/chat';
import styles from '../styles/ChatPage.module.scss';

async function readJson<T>(response: Response): Promise<T> {
  const body = await response.json();
  if (!response.ok) throw new Error(body.message || 'Không hoàn thành được yêu cầu.');
  return body as T;
}

export default function ChatPage() {
  const router = useRouter();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const bottom = useRef<HTMLDivElement>(null);

  const handleUnauthorized = useCallback((response: Response): boolean => {
    if (response.status !== 401) return false;
    void router.replace('/login?next=%2Fchat');
    return true;
  }, [router]);

  useEffect(() => {
    let active = true;
    fetch('/api/chat/conversations').then(async response => {
      if (handleUnauthorized(response)) return null;
      return readJson<Conversation[]>(response);
    }).then(items => {
      if (!active || !items) return;
      setConversations(items);
      if (items.length) setSelectedId(items[0].id);
    }).catch(reason => {
      if (active) setError(reason instanceof Error ? reason.message : 'Không tải được hội thoại.');
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [handleUnauthorized]);

  useEffect(() => {
    if (selectedId === null) { setMessages([]); return; }
    let active = true;
    setLoading(true);
    setError('');
    fetch(`/api/chat/conversations/${selectedId}`).then(async response => {
      if (handleUnauthorized(response)) return null;
      return readJson<ConversationDetail>(response);
    }).then(detail => { if (active && detail) setMessages(detail.messages); })
      .catch(reason => { if (active) setError(reason instanceof Error ? reason.message : 'Không tải được tin nhắn.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [selectedId, handleUnauthorized]);

  useEffect(() => { bottom.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, sending]);

  async function send(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = draft.trim();
    if (!message || sending || loading) return;
    const previous = messages;
    setMessages([...previous, { role: 'user', content: message, recommendedMovies: [] }]);
    setDraft('');
    setSending(true);
    setError('');
    try {
      const response = await fetch('/api/chat', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ conversationId: selectedId, message })
      });
      if (handleUnauthorized(response)) return;
      const reply = await readJson<ChatReply>(response);
      setMessages(current => [...current, {
        role: 'assistant', content: reply.reply, recommendedMovies: reply.recommendedMovies || [],
        createdAt: reply.createdAt
      }]);
      if (selectedId === null) setSelectedId(reply.conversationId);
      const listResponse = await fetch('/api/chat/conversations');
      if (listResponse.ok) setConversations(await readJson<Conversation[]>(listResponse));
    } catch (reason) {
      setMessages(previous);
      setDraft(message);
      setError(reason instanceof Error ? reason.message : 'Không gửi được tin nhắn.');
    } finally {
      setSending(false);
    }
  }

  async function removeConversation(id: number) {
    setError('');
    try {
      const response = await fetch(`/api/chat/conversations/${id}`, { method: 'DELETE' });
      if (handleUnauthorized(response)) return;
      await readJson<string>(response);
      const remaining = conversations.filter(item => item.id !== id);
      setConversations(remaining);
      if (selectedId === id) { setSelectedId(null); setMessages([]); }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Không xóa được hội thoại.');
    }
  }

  return <>
    <Head><title>Chat gợi ý phim | WhatToWatch</title></Head>
    <Layout><main className={styles.page}>
      <header className={styles.heading}>
        <div><span className={styles.eyebrow}>WHAT TO WATCH</span><h1>Trợ lý gợi ý phim</h1>
          <p>Hỏi về phim, rồi tiếp tục câu chuyện trong cùng một hội thoại.</p></div>
      </header>
      <div className={styles.shell}>
        <aside className={styles.sidebar} aria-label='Các cuộc hội thoại'>
          <button className={styles.newChat} type='button' disabled={sending} onClick={() => {
            setSelectedId(null); setMessages([]); setError('');
          }}>+ Cuộc trò chuyện mới</button>
          <h2>Gần đây</h2>
          {conversations.length === 0 && <p>Chưa có cuộc hội thoại.</p>}
          <ul>{conversations.map(item => <li key={item.id} className={selectedId === item.id ? styles.selected : ''}>
            <button type='button' disabled={sending} onClick={() => setSelectedId(item.id)}
              aria-current={selectedId === item.id ? 'true' : undefined}>{item.title}</button>
            <button type='button' className={styles.delete} disabled={sending}
              aria-label={`Xóa cuộc hội thoại ${item.title}`} onClick={() => void removeConversation(item.id)}>×</button>
          </li>)}</ul>
        </aside>
        <section className={styles.chat} aria-label='Nội dung hội thoại'>
          <div className={styles.feed} aria-live='polite'>
            {loading && <p role='status'>Đang tải hội thoại…</p>}
            {!loading && messages.length === 0 && <div className={styles.empty}>
              <h2>Hôm nay xem phim gì?</h2>
              <p>Thử hỏi: “Gợi ý phim khoa học viễn tưởng”, sau đó hỏi “Phim đó phát hành năm nào?”</p>
            </div>}
            {messages.map((item, index) => <article key={item.id || `${item.role}-${index}`}
              className={item.role === 'user' ? styles.userMessage : styles.assistantMessage}>
              <span className={styles.speaker}>{item.role === 'user' ? 'Bạn' : 'WhatToWatch'}</span>
              <p>{item.content}</p>
              {item.recommendedMovies?.length > 0 && <ul className={styles.movies}>{item.recommendedMovies.map(movie =>
                <li key={movie.movie_id}>
                  <Link href={`/movies/${encodeURIComponent(movie.movie_id)}`}><a>{movie.title} →</a></Link>
                  <span>{movie.reason}</span>
                </li>)}</ul>}
            </article>)}
            {sending && <p role='status' className={styles.waiting}>Đang tìm phim và soạn câu trả lời…</p>}
            <div ref={bottom} />
          </div>
          <form className={styles.composer} onSubmit={send}>
            {error && <p role='alert' className={styles.error}>{error}</p>}
            <label htmlFor='chat-message'>Tin nhắn của bạn</label>
            <div><input id='chat-message' value={draft} onChange={event => setDraft(event.target.value)}
              placeholder='Bạn muốn xem phim như thế nào?' maxLength={2000} disabled={sending || loading} />
              <button type='submit' disabled={!draft.trim() || sending || loading}>Gửi</button></div>
          </form>
        </section>
      </div>
    </main></Layout>
  </>;
}
