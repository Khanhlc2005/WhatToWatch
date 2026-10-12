import Head from 'next/head';
import Link from 'next/link';
import { FormEvent, useCallback, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '../components/Layout';
import { ChatMessage, ChatReply, Conversation, ConversationDetail } from '../lib/chat';
import styles from '../styles/ChatPage.module.scss';

async function readJson<T>(response: Response): Promise<T> {
  const body = await response.json();
  if (!response.ok) throw new Error(body.message || 'Could not complete the request.');
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
      if (active) setError(reason instanceof Error ? reason.message : 'Could not load conversations.');
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
      .catch(reason => { if (active) setError(reason instanceof Error ? reason.message : 'Could not load messages.'); })
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
      setError(reason instanceof Error ? reason.message : 'Could not send your message.');
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
      setError(reason instanceof Error ? reason.message : 'Could not delete the conversation.');
    }
  }

  return <>
    <Head><title>Chatbot W2W | WhatToWatch</title></Head>
    <Layout><main className={styles.page}>
      <header className={styles.heading}>
        <div><span className={styles.eyebrow}>WHAT TO WATCH</span><h1>Your movie assistant</h1>
          <p>Ask about movies and continue the conversation in one place.</p></div>
      </header>
      <div className={styles.shell}>
        <aside className={styles.sidebar} aria-label='Conversations'>
          <button className={styles.newChat} type='button' disabled={sending} onClick={() => {
            setSelectedId(null); setMessages([]); setError('');
          }}>+ New conversation</button>
          <h2>Recent</h2>
          {conversations.length === 0 && <p>No conversations yet.</p>}
          <ul>{conversations.map(item => <li key={item.id} className={selectedId === item.id ? styles.selected : ''}>
            <button type='button' disabled={sending} onClick={() => setSelectedId(item.id)}
              aria-current={selectedId === item.id ? 'true' : undefined}>{item.title}</button>
            <button type='button' className={styles.delete} disabled={sending}
              aria-label={`Delete conversation ${item.title}`} onClick={() => void removeConversation(item.id)}>×</button>
          </li>)}</ul>
        </aside>
        <section className={styles.chat} aria-label='Conversation'>
          <div className={styles.feed} aria-live='polite'>
            {loading && <p role='status'>Loading conversation…</p>}
            {!loading && messages.length === 0 && <div className={styles.empty}>
              <h2>What should you watch today?</h2>
              <p>Try asking: “Recommend a science fiction movie,” then “When was it released?”</p>
            </div>}
            {messages.map((item, index) => <article key={item.id || `${item.role}-${index}`}
              className={item.role === 'user' ? styles.userMessage : styles.assistantMessage}>
              <span className={styles.speaker}>{item.role === 'user' ? 'You' : 'WhatToWatch'}</span>
              <p>{item.content}</p>
              {item.recommendedMovies?.length > 0 && <ul className={styles.movies}>{item.recommendedMovies.map(movie =>
                <li key={movie.movie_id}>
                  <Link href={`/movies/${encodeURIComponent(movie.movie_id)}`}><a>{movie.title} →</a></Link>
                  <span>{movie.reason}</span>
                </li>)}</ul>}
            </article>)}
            {sending && <p role='status' className={styles.waiting}>Finding movies and writing a reply…</p>}
            <div ref={bottom} />
          </div>
          <form className={styles.composer} onSubmit={send}>
            {error && <p role='alert' className={styles.error}>{error}</p>}
            <label htmlFor='chat-message'>Your message</label>
            <div><input id='chat-message' value={draft} onChange={event => setDraft(event.target.value)}
              placeholder='What kind of movie would you like to watch?' maxLength={2000} disabled={sending || loading} />
              <button type='submit' disabled={!draft.trim() || sending || loading}>Send</button></div>
          </form>
        </section>
      </div>
    </main></Layout>
  </>;
}
