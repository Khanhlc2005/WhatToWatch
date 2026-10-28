import Head from 'next/head';
import { FormEvent, useCallback, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '../components/Layout';
import { ChatMessage, ChatReply, Conversation, ConversationDetail } from '../lib/chat';
import { formatClock } from '../lib/apiTime';
import ChatComposer from '../components/chat/ChatComposer';
import ChatMessageView from '../components/chat/ChatMessage';
import ConversationList from '../components/chat/ConversationList';
import StatusNote from '../components/ui/StatusNote';
import page from '../styles/Page.module.scss';
import styles from '../styles/ChatPage.module.scss';

const suggestions = [
  'Recommend a science fiction movie',
  'Something short and funny for tonight',
  'Korean thrillers like Parasite'
];

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
    setMessages([...previous, { role: 'user', content: message, recommendedMovies: [], createdAt: new Date().toISOString() }]);
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
        createdAt: reply.createdAt, status: reply.status
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
    <Layout><main className={`${page.page} ${page.tight}`}>
      <header className={page.head}>
        <span className={page.eyebrow}>WHAT TO WATCH</span>
        <h1>Your movie assistant</h1>
        <p>Ask about movies and continue the conversation in one place.</p>
      </header>
      <div className={styles.shell}>
        <ConversationList items={conversations} selected={selectedId} busy={sending}
          onNew={() => { setSelectedId(null); setMessages([]); setError(''); }}
          onSelect={setSelectedId} onDelete={id => void removeConversation(id)} />
        <section className={styles.chat} aria-label='Conversation'>
          <div className={styles.feed} aria-live='polite'>
            {loading && <StatusNote tone='loading'>Loading conversation…</StatusNote>}
            {!loading && messages.length === 0 && <div className={styles.empty}>
              <h2>What should you watch today?</h2>
              <p>Try asking: “Recommend a science fiction movie,” then “When was it released?”</p>
            </div>}
            {messages.map((item, index) => <ChatMessageView key={item.id || `${item.role}-${index}`}
              role={item.role} content={item.content} time={formatClock(item.createdAt)}
              movies={item.recommendedMovies} status={item.status} />)}
            <div ref={bottom} />
          </div>
          <ChatComposer value={draft} onChange={setDraft} onSend={send} sending={sending} loading={loading} error={error}
            suggestions={!loading && messages.length === 0 ? suggestions : undefined} />
        </section>
      </div>
    </main></Layout>
  </>;
}
