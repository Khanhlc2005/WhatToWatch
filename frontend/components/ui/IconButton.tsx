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

const IconButton = React.forwardRef<HTMLButtonElement, IconButtonProps>(function IconButton(
  { icon, label, variant, size = 'md', filled, className, ...rest }, ref
) {
  const classes = [styles.iconButton, variant && styles[variant], size === 'lg' && styles.large, className]
    .filter(Boolean).join(' ');
  return <button ref={ref} type='button' {...rest} className={classes} aria-label={label} title={label}>
    <Icon name={icon} filled={filled} size={size === 'lg' ? 22 : 18} />
  </button>;
});

export default IconButton;
