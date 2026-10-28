import React from 'react';
import styles from '../../styles/ui/TextField.module.scss';

export interface TextFieldProps extends React.InputHTMLAttributes<HTMLInputElement> {
  id: string;
  label?: string;
  error?: string;
  hint?: string;
  trailing?: React.ReactNode;
}

export default function TextField({ id, label, error, hint, trailing, className, ...input }: TextFieldProps): React.ReactElement {
  const noteId = error || hint ? id + '-note' : undefined;
  return <div className={`${styles.field} ${error ? styles.invalid : ''} ${className || ''}`}>
    {label && <label htmlFor={id}>{label}</label>}
    <div className={styles.wrap}>
      <input id={id} className={styles.input} aria-invalid={error ? true : undefined} aria-describedby={noteId} {...input} />
      {trailing}
    </div>
    {error ? <span id={noteId} className={styles.error} role='alert'>{error}</span>
      : hint ? <span id={noteId} className={styles.hint}>{hint}</span> : null}
  </div>;
}
