import { Conversation } from '../../lib/chat';
import { formatWhen } from '../../lib/apiTime';
import Button from '../ui/Button';
import IconButton from '../ui/IconButton';
import styles from '../../styles/ConversationList.module.scss';

export interface ConversationListProps {
  items: Conversation[];
  selected: number | null;
  // Disables everything while a reply is in flight.
  busy: boolean;
  onNew: () => void;
  onSelect: (id: number) => void;
  onDelete: (id: number) => void;
}

export default function ConversationList({ items, selected, busy, onNew, onSelect, onDelete }: ConversationListProps): React.ReactElement {
  return <aside className={styles.list} aria-label='Conversations'>
    <Button variant='primary' icon='plus' block disabled={busy} onClick={onNew}>New conversation</Button>
    <h2 className={styles.heading}>RECENT</h2>
    {items.length === 0 && <p className={styles.empty}>No conversations yet.</p>}
    <ul>
      {items.map(item => {
        const on = item.id === selected;
        const when = formatWhen(item.updatedAt);
        return <li key={item.id} className={on ? styles.on : undefined}>
          <button type='button' className={styles.item} disabled={busy} aria-current={on ? 'true' : undefined}
            onClick={() => onSelect(item.id)}>
            <span className={styles.title}>{item.title}</span>
            {when && <span className={styles.when}>{when}</span>}
          </button>
          <IconButton icon='trash' label={`Delete conversation ${item.title}`} variant='danger' disabled={busy}
            onClick={() => onDelete(item.id)} />
        </li>;
      })}
    </ul>
  </aside>;
}
