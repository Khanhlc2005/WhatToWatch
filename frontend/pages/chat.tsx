import Head from 'next/head';
import Link from 'next/link';
import { FormEvent, useEffect, useState } from 'react';
import Layout from '../components/Layout';
import styles from '../styles/Chat.module.scss';

type Movie = { movieId: string; title: string; reason: string };
type ChatResult = { conversationId: number; reply: string; recommendedMovies: Movie[] };
type Message = { role: 'user' | 'assistant'; text: string; movies?: Movie[] };

export default function Chat() {
  const [authenticated, setAuthenticated] = useState<boolean | null>(null);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch('/api/auth/session').then(response => response.json())
      .then(body => setAuthenticated(Boolean(body.authenticated)))
      .catch(() => setAuthenticated(false));
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const message = input.trim();
    if (!message || loading) return;
    setInput('');
    setError('');
    setMessages(previous => [...previous, { role: 'user', text: message }]);
    setLoading(true);
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, conversationId })
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.message || 'Không thể kết nối AI.');
      const result = body as ChatResult;
      setConversationId(result.conversationId);
      setMessages(previous => [...previous, {
        role: 'assistant', text: result.reply, movies: result.recommendedMovies || []
      }]);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Không thể kết nối AI.');
    } finally {
      setLoading(false);
    }
  }

  return <>
    <Head><title>Tư vấn phim cùng AI | WhatToWatch</title></Head>
    <Layout><main className={styles.page}>
      <span className={styles.eyebrow}>WHAT TO WATCH AI</span>
      <h1>Tìm phim hợp tâm trạng</h1>
      <p>Cho tôi biết bạn muốn xem thể loại, bối cảnh hoặc cảm giác gì tối nay.</p>
      {authenticated === false ? <p className={styles.notice}>
        <Link href='/login'><a>Đăng nhập</a></Link> để bắt đầu trò chuyện với AI.
      </p> : <>
        <div className={styles.messages} aria-live='polite'>
          {messages.length === 0 && <p className={styles.hint}>Ví dụ: Gợi ý phim khoa học viễn tưởng nhẹ nhàng để xem cuối tuần.</p>}
          {messages.map((item, index) => <div key={index} className={`${styles.message} ${item.role === 'user' ? styles.user : styles.assistant}`}>
            <strong>{item.role === 'user' ? 'Bạn' : 'AI tư vấn phim'}</strong>
            <p>{item.text}</p>
            {item.movies && item.movies.length > 0 && <ul>{item.movies.map(movie => <li key={movie.movieId}>
              <strong>{movie.title}</strong>{movie.reason && <span> — {movie.reason}</span>}
            </li>)}</ul>}
          </div>)}
          {loading && <p role='status' className={styles.hint}>AI đang tìm phim và chuẩn bị câu trả lời. Trên CPU có thể mất vài phút…</p>}
        </div>
        {error && <p role='alert' className={styles.error}>{error}</p>}
        <form onSubmit={submit} className={styles.form}>
          <label htmlFor='chat-message'>Tin nhắn của bạn</label>
          <div><input id='chat-message' value={input} onChange={event => setInput(event.target.value)}
            maxLength={500} placeholder='Bạn muốn xem phim gì?' disabled={loading || authenticated === null} />
            <button type='submit' disabled={loading || !input.trim() || authenticated === null}>Gửi</button></div>
        </form>
      </>}
    </main></Layout>
  </>;
}
