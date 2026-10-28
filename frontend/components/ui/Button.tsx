import Link from 'next/link';
import React from 'react';
import styles from '../../styles/ui/Button.module.scss';
import Icon, { IconName } from './Icon';

type Variant = 'primary' | 'secondary' | 'ghost' | 'ghost-danger';

interface Shared {
  variant?: Variant;
  size?: 'sm' | 'md';
  icon?: IconName;
  iconRight?: IconName;
  iconFilled?: boolean;
  busy?: boolean;
  busyLabel?: string;
  pressed?: boolean;
  block?: boolean;
}

export type ButtonProps = Shared & React.ButtonHTMLAttributes<HTMLButtonElement> & { href?: undefined };
export type LinkButtonProps = Shared & React.AnchorHTMLAttributes<HTMLAnchorElement> & { href: string };

export function buttonClass(props: Shared & { className?: string }): string {
  const { variant = 'secondary', size = 'md', block, className } = props;
  return [styles.button, styles[variant === 'ghost-danger' ? 'ghostDanger' : variant], size === 'sm' && styles.small,
    block && styles.block, className].filter(Boolean).join(' ');
}

// Labels are sentence case and verb first. One `primary` per view.
export default function Button(props: ButtonProps | LinkButtonProps): React.ReactElement {
  const { variant, size, icon, iconRight, iconFilled, busy, busyLabel, pressed, block, className, children, ...rest } = props;
  const content = <>
    {icon && <Icon name={icon} filled={iconFilled} />}
    <span>{busy && busyLabel ? busyLabel : children}</span>
    {iconRight && <Icon name={iconRight} />}
  </>;
  const classes = buttonClass({ variant, size, block, className });

  if ('href' in props && props.href !== undefined) {
    const { href, ...anchor } = rest as React.AnchorHTMLAttributes<HTMLAnchorElement> & { href: string };
    if (href.startsWith('/')) return <Link href={href}><a {...anchor} className={classes}>{content}</a></Link>;
    return <a {...anchor} href={href} className={classes}>{content}</a>;
  }
  const button = rest as React.ButtonHTMLAttributes<HTMLButtonElement>;
  return <button
    type='button'
    {...button}
    className={classes}
    disabled={busy || button.disabled}
    aria-busy={busy || undefined}
    aria-pressed={pressed}
  >{content}</button>;
}
