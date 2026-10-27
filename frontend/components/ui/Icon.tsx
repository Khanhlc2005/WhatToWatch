import {
  AlertTriangle, ArrowUpRight, Bookmark, Check, ChevronDown, ChevronLeft, ChevronRight, Clock, Edit3, Film, Heart,
  Home, Info, List, LogOut, MessageSquare, Play, Plus, Search, Send, SlidersHorizontal, Sparkles, Star, Trash2, User, X
} from 'lucide-react';

const icons = {
  search: Search,
  info: Info,
  x: X,
  'chevron-left': ChevronLeft,
  'chevron-right': ChevronRight,
  'chevron-down': ChevronDown,
  plus: Plus,
  check: Check,
  heart: Heart,
  star: Star,
  play: Play,
  send: Send,
  trash: Trash2,
  sliders: SlidersHorizontal,
  clock: Clock,
  list: List,
  message: MessageSquare,
  home: Home,
  bookmark: Bookmark,
  user: User,
  'log-out': LogOut,
  edit: Edit3,
  'arrow-up-right': ArrowUpRight,
  film: Film,
  alert: AlertTriangle,
  sparkle: Sparkles
};

export type IconName = keyof typeof icons;

export interface IconProps {
  name: IconName;
  size?: number;
  filled?: boolean;
  label?: string;
  className?: string;
}

// Stroked Lucide set (24px grid, 1.5 stroke). `filled` is only for "on" states (heart, star) and play.
export default function Icon({ name, size = 18, filled = false, label, className }: IconProps): React.ReactElement {
  const Glyph = icons[name];
  return <Glyph
    className={className}
    size={size}
    strokeWidth={1.5}
    fill={filled ? 'currentColor' : 'none'}
    style={{ flex: 'none', display: 'block' }}
    {...(label ? { role: 'img', 'aria-label': label } : { 'aria-hidden': true })}
  />;
}
