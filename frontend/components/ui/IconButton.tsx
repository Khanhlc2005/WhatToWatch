import React from 'react';
import styles from '../../styles/ui/IconButton.module.scss';
import Icon, { IconName } from './Icon';

export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  icon: IconName;
  label: string;
  variant?: 'float' | 'danger';
  size?: 'md' | 'lg';
  filled?: boolean;
}

export default function IconButton({ icon, label, variant, size = 'md', filled, className, ...rest }: IconButtonProps): React.ReactElement {
  const classes = [styles.iconButton, variant && styles[variant], size === 'lg' && styles.large, className]
    .filter(Boolean).join(' ');
  return <button type='button' {...rest} className={classes} aria-label={label} title={label}>
    <Icon name={icon} filled={filled} size={size === 'lg' ? 22 : 18} />
  </button>;
}
