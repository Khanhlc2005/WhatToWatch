import Link from 'next/link';
import { ChatStatus, RecommendedMovie } from '../../lib/chat';
import Icon from '../ui/Icon';
import Perforation from '../ui/Perforation';
import StatusNote, { StatusNoteProps } from '../ui/StatusNote';
import styles from '../../styles/ChatMessage.module.scss';

export interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  time?: string;
  movies?: RecommendedMovie[];
  status?: ChatStatus;
}

// Each reply status that is not a normal answer gets its own note; `error` also gets a danger border.
const statusNotes: Record<Exclude<ChatStatus, 'answered'>, { tone: StatusNoteProps['tone']; text: string }> = {
  no_match: { tone: 'empty', text: 'No movie in the collection matched that. Try a different genre, decade or mood.' },
  insufficient_context: { tone: 'info', text: 'I need a little more to go on. Which movie do you mean, or what are you in the mood for?' },
  error: { tone: 'error', text: 'Something went wrong while writing this reply. Send your message again.' }
};

export default function ChatMessage({ role, content, time, movies = [], status }: ChatMessageProps): React.ReactElement {
  const user = role === 'user';
  const note = !user && status && status !== 'answered' ? statusNotes[status] : null;
  const classes = [styles.message, user ? styles.user : styles.bot, !user && status === 'error' && styles.failed]
    .filter(Boolean).join(' ');
  return <article className={classes}>
    <span className={styles.who}>
      {user ? 'You' : 'WhatToWatch'}
      {time && <span className={styles.time}>{time}</span>}
    </span>
    {content && <p>{content}</p>}
    {note && <StatusNote tone={note.tone}>{note.text}</StatusNote>}
    {movies.length > 0 && <>
      <Perforation inset />
      <ol className={styles.picks}>
        {movies.map((movie, index) => <li key={movie.movie_id}>
          <span className={styles.num}>{index < 9 ? '0' : ''}{index + 1}</span>
          <div>
            <Link href={`/movies/${encodeURIComponent(movie.movie_id)}`}>
              <a className={styles.link}>{movie.title}<Icon name='arrow-up-right' size={14} /></a>
            </Link>
            <span className={styles.reason}>{movie.reason}</span>
          </div>
        </li>)}
      </ol>
    </>}
  </article>;
}
