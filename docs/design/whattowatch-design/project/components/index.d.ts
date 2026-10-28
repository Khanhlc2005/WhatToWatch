import type * as React from 'react';

export interface Movie { id: string; title: string; poster?: string; backdrop?: string; art?: [string, string]; rating: number | null; year?: number | string; runtime?: number | null; overview?: string; genres?: string[]; cast?: string | null; favorite?: boolean; watchLater?: boolean; myRating?: number | null }
export type IconName = 'search' | 'info' | 'x' | 'chevron-left' | 'chevron-right' | 'chevron-down' | 'plus' | 'check' | 'heart' | 'star' | 'play' | 'send' | 'trash' | 'sliders' | 'clock' | 'list' | 'message' | 'home' | 'bookmark' | 'user' | 'log-out' | 'edit' | 'arrow-up-right' | 'film' | 'alert' | 'sparkle';

export interface BrandProps { href?: string; size?: 'md' | 'lg'; markOnly?: boolean }
export interface IconProps { name: IconName; size?: number; filled?: boolean; label?: string; className?: string }
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> { variant?: 'primary' | 'secondary' | 'ghost' | 'ghost-danger'; size?: 'sm' | 'md'; icon?: IconName; iconRight?: IconName; iconFilled?: boolean; busy?: boolean; busyLabel?: string; href?: string; pressed?: boolean }
export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> { icon: IconName; label: string; variant?: 'float' | 'danger'; size?: 'md' | 'lg'; filled?: boolean }
export interface ChipProps { selected?: boolean; onClick?: () => void; children?: React.ReactNode }
export interface PerforationProps { inset?: boolean }
export interface TicketMetaProps { rating?: number | null; year?: number | string; runtime?: number | null; extra?: string[]; highlight?: boolean; className?: string }
export interface StatusNoteProps { tone?: 'loading' | 'info' | 'invite' | 'error' | 'success' | 'empty'; title?: string; action?: React.ReactNode; block?: boolean; children?: React.ReactNode }
export interface NavbarProps { active?: 'home' | 'search' | 'discover' | 'chat' | 'library'; scrolled?: boolean; user?: { email: string } | null; menuOpen?: boolean; onSignOut?: () => void }
export interface TabsProps { items: { id: string; label: string; href: string; count?: number }[]; active: string; label: string; onChange?: (id: string) => void }
export interface PaginationProps { page: number; totalPages: number; onChange?: (page: number) => void }
export interface PosterProps { movie: Partial<Movie> }
export interface MovieCardProps { movie: Movie; reason?: string; rank?: number; onOpen?: () => void; hideActions?: boolean; signedIn?: boolean }
export interface SectionHeadingProps { title: string; id?: string; stamp?: string; count?: string }
export interface MovieRowProps { movies: Movie[]; title?: string; id?: string; stamp?: string; count?: string; note?: React.ReactNode; reasons?: string[]; ranked?: boolean; signedIn?: boolean }
export interface SkeletonRowProps { count?: number; label?: string }
export interface HeroProps { movie?: Movie; onOpen?: () => void; signedIn?: boolean }
export interface LibraryActionsProps { favorite?: boolean; watchLater?: boolean; compact?: boolean; signedIn?: boolean; busy?: boolean; error?: string; onChange?: (kind: 'fav' | 'later', on: boolean) => void; onRequireSignIn?: () => void }
export interface AddToListProps { lists: { id: string; name: string; count: number; checked?: boolean }[]; open?: boolean; creating?: boolean; signedIn?: boolean; busy?: boolean; error?: string; onToggle?: (id: string, on: boolean) => void; onCreate?: (name: string) => void; onRequireSignIn?: () => void }
export interface RatingStarsProps { value?: number | null; onRate?: (value: number) => void; state?: 'loading' | 'signed-out'; busy?: boolean; error?: string }
export interface MovieDetailProps { movie: Movie; trailer?: 'image' | 'playing' | 'none' | 'error'; similar?: Movie[]; lists?: AddToListProps['lists']; listsOpen?: boolean; signedIn?: boolean; onClose?: () => void; inline?: boolean }
export interface TextFieldProps extends React.InputHTMLAttributes<HTMLInputElement> { label?: string; error?: string; hint?: string; trailing?: React.ReactNode }
export interface SearchFormProps { value?: string; onSearch?: (query: string) => void }
export interface AuthFormProps { mode: 'login' | 'register'; registered?: boolean; mismatch?: boolean; error?: string; busy?: boolean; email?: string }
export interface ConversationListProps { items: { id: number; title: string; when?: string }[]; selected?: number | null; busy?: boolean; onNew?: () => void; onSelect?: (id: number) => void; onDelete?: (id: number) => void }
export interface ChatMessageProps { role: 'user' | 'assistant'; content?: string; time?: string; movies?: { id: string; title: string; reason: string }[]; status?: 'answered' | 'no_match' | 'insufficient_context' | 'error' }
export interface ChatComposerProps { value?: string; suggestions?: string[]; sending?: boolean; loading?: boolean; error?: string; onSend?: (text: string) => void }
export interface FilterPanelProps { genres: { id: number; name: string }[]; selectedGenres?: number[]; yearFrom?: number; yearTo?: number; minRating?: number; maxRating?: number; minRuntime?: number; maxRuntime?: number; language?: string; onApply?: () => void }
export interface RatingHistoryProps { items: { id: number; rating: number; date: string; movie: Movie }[] }
export interface WatchHistoryProps { total: number; groups: { label: string; items: { id: number; time: string; movie: Movie }[] }[] }
export interface WatchlistManagerProps { lists: { id: string; name: string; count: number; system?: boolean; movies?: Movie[] }[]; selected?: string; creating?: boolean }

export declare function Brand(props: BrandProps): React.ReactElement;
export declare function Icon(props: IconProps): React.ReactElement;
export declare function Button(props: ButtonProps): React.ReactElement;
export declare function IconButton(props: IconButtonProps): React.ReactElement;
export declare function Chip(props: ChipProps): React.ReactElement;
export declare function Perforation(props: PerforationProps): React.ReactElement;
export declare function TicketMeta(props: TicketMetaProps): React.ReactElement;
export declare function StatusNote(props: StatusNoteProps): React.ReactElement;
export declare function Navbar(props: NavbarProps): React.ReactElement;
export declare function Tabs(props: TabsProps): React.ReactElement;
export declare function Pagination(props: PaginationProps): React.ReactElement;
export declare function Footer(): React.ReactElement;
export declare function Poster(props: PosterProps): React.ReactElement;
export declare function MovieCard(props: MovieCardProps): React.ReactElement;
export declare function SectionHeading(props: SectionHeadingProps): React.ReactElement;
export declare function MovieRow(props: MovieRowProps): React.ReactElement;
export declare function SkeletonRow(props: SkeletonRowProps): React.ReactElement;
export declare function Hero(props: HeroProps): React.ReactElement;
export declare function LibraryActions(props: LibraryActionsProps): React.ReactElement;
export declare function AddToList(props: AddToListProps): React.ReactElement;
export declare function RatingStars(props: RatingStarsProps): React.ReactElement;
export declare function MovieDetail(props: MovieDetailProps): React.ReactElement;
export declare function TextField(props: TextFieldProps): React.ReactElement;
export declare function SearchForm(props: SearchFormProps): React.ReactElement;
export declare function AuthForm(props: AuthFormProps): React.ReactElement;
export declare function ConversationList(props: ConversationListProps): React.ReactElement;
export declare function ChatMessage(props: ChatMessageProps): React.ReactElement;
export declare function ChatComposer(props: ChatComposerProps): React.ReactElement;
export declare function FilterPanel(props: FilterPanelProps): React.ReactElement;
export declare function RatingHistory(props: RatingHistoryProps): React.ReactElement;
export declare function WatchHistory(props: WatchHistoryProps): React.ReactElement;
export declare function WatchlistManager(props: WatchlistManagerProps): React.ReactElement;
