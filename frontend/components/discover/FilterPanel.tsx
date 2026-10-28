import { FormEvent, useEffect, useState } from 'react';
import { DiscoverFilters, emptyFilters, languages, movieGenres } from '../../lib/discover';
import Button from '../ui/Button';
import Chip from '../ui/Chip';
import Icon from '../ui/Icon';
import TextField from '../ui/TextField';
import styles from '../../styles/FilterPanel.module.scss';

export interface FilterPanelProps {
  applied: DiscoverFilters;
  ratingEnabled: boolean;
  genresEnabled: boolean;
  onApply: (filters: DiscoverFilters) => void;
}

interface RangeProps {
  id: string;
  legend: string;
  from: string;
  to: string;
  min: number;
  max: number;
  step?: number;
  unit?: string;
  disabled?: boolean;
  hint?: string;
  onChange: (from: string, to: string) => void;
}

function RangeFields({ id, legend, from, to, min, max, step, unit, disabled, hint, onChange }: RangeProps) {
  return <fieldset className={styles.fieldset} disabled={disabled}>
    <legend>{legend}</legend>
    <div className={styles.range}>
      <TextField id={id + '-from'} label='From' type='number' inputMode='decimal' min={min} max={max} step={step}
        value={from} placeholder={String(min)} onChange={event => onChange(event.target.value, to)} />
      <span className={styles.dash} aria-hidden='true'>–</span>
      <TextField id={id + '-to'} label='To' type='number' inputMode='decimal' min={min} max={max} step={step}
        value={to} placeholder={String(max)} onChange={event => onChange(from, event.target.value)} />
      {unit && <span className={styles.unit}>{unit}</span>}
    </div>
    {hint && <p className={styles.hint}>{hint}</p>}
  </fieldset>;
}

export default function FilterPanel({ applied, ratingEnabled, genresEnabled, onApply }: FilterPanelProps): React.ReactElement {
  const [draft, setDraft] = useState<DiscoverFilters>(applied);
  // Keep the form in step with the URL (back/forward, shared links, removing a chip).
  useEffect(() => setDraft(applied), [applied]);
  const set = <K extends keyof DiscoverFilters>(key: K, value: DiscoverFilters[K]) => setDraft(current => ({ ...current, [key]: value }));
  const toggleGenre = (id: number) => set('genreIds', draft.genreIds.includes(id) ? draft.genreIds.filter(item => item !== id) : [...draft.genreIds, id]);

  function submit(event: FormEvent) {
    event.preventDefault();
    onApply({
      ...draft,
      ...(ratingEnabled ? {} : { minRating: '', maxRating: '' }),
      ...(genresEnabled ? {} : { genreIds: [] })
    });
  }

  return <form className={styles.panel} onSubmit={submit}>
    <div className={styles.head}>
      <h2><Icon name='sliders' />Filters</h2>
      <button type='button' className={styles.reset} onClick={() => { setDraft(emptyFilters); onApply(emptyFilters); }}>Reset all</button>
    </div>
    <fieldset className={styles.fieldset} disabled={!genresEnabled}>
      <legend>Genres</legend>
      <div className={styles.chips}>
        {movieGenres.map(genre => <Chip key={genre.id} selected={draft.genreIds.includes(genre.id)} onClick={() => toggleGenre(genre.id)}>{genre.name}</Chip>)}
      </div>
      {!genresEnabled && <p className={styles.hint}>Paused until the catalogue has genre data.</p>}
    </fieldset>
    <RangeFields id='year' legend='Release year' min={1920} max={2026} from={draft.yearFrom} to={draft.yearTo}
      onChange={(from, to) => setDraft(current => ({ ...current, yearFrom: from, yearTo: to }))} />
    <RangeFields id='rating' legend='IMDb rating' min={0} max={10} step={0.1} unit='/ 10' from={draft.minRating} to={draft.maxRating}
      disabled={!ratingEnabled} hint={ratingEnabled ? undefined : 'Paused until the backend filters on the same IMDb score the cards show.'}
      onChange={(from, to) => setDraft(current => ({ ...current, minRating: from, maxRating: to }))} />
    <RangeFields id='runtime' legend='Runtime' min={0} max={300} unit='MIN' from={draft.minRuntime} to={draft.maxRuntime}
      onChange={(from, to) => setDraft(current => ({ ...current, minRuntime: from, maxRuntime: to }))} />
    <div className={styles.language}>
      <label htmlFor='filter-language'>Original language</label>
      <div className={styles.select}>
        <select id='filter-language' value={draft.language} onChange={event => set('language', event.target.value)}>
          {languages.map(([code, name]) => <option key={code} value={code}>{name}</option>)}
        </select>
        <Icon name='chevron-down' size={16} />
      </div>
    </div>
    <Button variant='primary' type='submit' block>
      {draft.genreIds.length ? `Show movies (${draft.genreIds.length} ${draft.genreIds.length === 1 ? 'genre' : 'genres'})` : 'Show movies'}
    </Button>
  </form>;
}
