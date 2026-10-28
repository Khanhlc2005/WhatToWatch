import { FormEvent } from 'react';
import Button from '../ui/Button';
import Chip from '../ui/Chip';
import Icon from '../ui/Icon';
import StatusNote from '../ui/StatusNote';
import styles from '../../styles/ChatComposer.module.scss';

export interface ChatComposerProps {
  value: string;
  onChange: (value: string) => void;
  onSend: (event: FormEvent<HTMLFormElement>) => void;
  // Shown on an empty conversation; a click fills the input.
  suggestions?: string[];
  sending: boolean;
  loading: boolean;
  error?: string;
}

export default function ChatComposer({ value, onChange, onSend, suggestions = [], sending, loading, error }: ChatComposerProps): React.ReactElement {
  const locked = sending || loading;
  return <form className={styles.composer} onSubmit={onSend}>
    {suggestions.length > 0 && <div className={styles.suggestions} role='group' aria-label='Suggestions'>
      {suggestions.map(text => <Chip key={text} onClick={() => onChange(text)}>{text}</Chip>)}
    </div>}
    {error && <StatusNote tone='error'>{error}</StatusNote>}
    <label htmlFor='chat-message' className={styles.label}>Your message</label>
    <div className={styles.bar}>
      <input id='chat-message' value={value} onChange={event => onChange(event.target.value)} maxLength={2000}
        disabled={locked} placeholder='What kind of movie would you like to watch?' autoComplete='off' />
      <Button variant='primary' type='submit' icon='send' disabled={!value.trim() || locked}>Send</Button>
    </div>
    {sending && <StatusNote tone='loading'>Finding movies and writing a reply…</StatusNote>}
  </form>;
}
