/* @ds-bundle: {"format":4,"namespace":"WTW","components":[{"name":"Brand"},{"name":"Icon"},{"name":"Button"},{"name":"IconButton"},{"name":"Chip"},{"name":"Perforation"},{"name":"TicketMeta"},{"name":"StatusNote"},{"name":"Navbar"},{"name":"Tabs"},{"name":"Pagination"},{"name":"Footer"},{"name":"Poster"},{"name":"MovieCard"},{"name":"SectionHeading"},{"name":"MovieRow"},{"name":"SkeletonRow"},{"name":"Hero"},{"name":"LibraryActions"},{"name":"AddToList"},{"name":"RatingStars"},{"name":"MovieDetail"},{"name":"TextField"},{"name":"SearchForm"},{"name":"AuthForm"},{"name":"ConversationList"},{"name":"ChatMessage"},{"name":"ChatComposer"},{"name":"FilterPanel"},{"name":"RatingHistory"},{"name":"WatchHistory"},{"name":"WatchlistManager"}]} */
(function () {
  var R = window.React;
  var h = R.createElement;
  var useState = R.useState, useRef = R.useRef, useEffect = R.useEffect;

  function cx() {
    var out = [];
    for (var i = 0; i < arguments.length; i++) if (arguments[i]) out.push(arguments[i]);
    return out.join(' ');
  }
  function rest(props, omit) {
    var o = {};
    for (var k in props) if (omit.indexOf(k) < 0) o[k] = props[k];
    return o;
  }

  /* ---------- Icon: 24px grid, 1.5 stroke, round caps (Lucide style) ---------- */
  var PATHS = {
    search: ['M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14z', 'M20 20l-4.2-4.2'],
    info: ['M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z', 'M12 16v-5', 'M12 8h.01'],
    x: ['M18 6L6 18', 'M6 6l12 12'],
    'chevron-left': ['M15 18l-6-6 6-6'],
    'chevron-right': ['M9 18l6-6-6-6'],
    'chevron-down': ['M6 9l6 6 6-6'],
    plus: ['M12 5v14', 'M5 12h14'],
    check: ['M20 6L9 17l-5-5'],
    heart: ['M19.5 12.6L12 20l-7.5-7.4A4.6 4.6 0 0 1 12 6.5a4.6 4.6 0 0 1 7.5 6.1z'],
    star: ['M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.9l-5.2 2.7 1-5.8-4.3-4.1 5.9-.9z'],
    play: ['M7 4.5v15l12-7.5z'],
    send: ['M21 3L10 14', 'M21 3l-7 18-4-7-7-4z'],
    trash: ['M4 7h16', 'M9 7V4h6v3', 'M6 7l1 13h10l1-13'],
    sliders: ['M4 6h10', 'M18 6h2', 'M16 4v4', 'M4 12h4', 'M12 12h8', 'M10 10v4', 'M4 18h12', 'M20 18h0', 'M18 16v4'],
    clock: ['M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z', 'M12 7v5l3 2'],
    list: ['M9 6h11', 'M9 12h11', 'M9 18h11', 'M4.5 6h.01', 'M4.5 12h.01', 'M4.5 18h.01'],
    message: ['M20 15a2 2 0 0 1-2 2H8l-4 4V5a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2z'],
    home: ['M4 10.5L12 4l8 6.5V20h-5v-6H9v6H4z'],
    bookmark: ['M6 3.5h12V21l-6-4-6 4z'],
    user: ['M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8z', 'M4 21a8 8 0 0 1 16 0'],
    'log-out': ['M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4', 'M16 17l5-5-5-5', 'M21 12H9'],
    edit: ['M4 20h4L19 9l-4-4L4 16z', 'M13.5 6.5l4 4'],
    'arrow-up-right': ['M7 17L17 7', 'M8 7h9v9'],
    film: ['M4 4h16v16H4z', 'M8 4v16', 'M16 4v16', 'M4 8h4', 'M4 12h4', 'M4 16h4', 'M16 8h4', 'M16 12h4', 'M16 16h4'],
    alert: ['M12 3l9.5 17h-19z', 'M12 10v4', 'M12 17h.01'],
    sparkle: ['M12 3v4', 'M12 17v4', 'M3 12h4', 'M17 12h4', 'M6 6l2.5 2.5', 'M15.5 15.5L18 18', 'M18 6l-2.5 2.5', 'M8.5 15.5L6 18']
  };
  function Icon(props) {
    var size = props.size || 18;
    var filled = props.filled;
    var paths = PATHS[props.name] || [];
    return h('svg', {
      className: cx('w-icon', props.className), width: size, height: size, viewBox: '0 0 24 24',
      fill: filled ? 'currentColor' : 'none', stroke: 'currentColor', strokeWidth: 1.5,
      strokeLinecap: 'round', strokeLinejoin: 'round', 'aria-hidden': props.label ? undefined : 'true',
      role: props.label ? 'img' : undefined, 'aria-label': props.label
    }, paths.map(function (d, i) { return h('path', { key: i, d: d }); }));
  }

  /* ---------- Brand ---------- */
  function Mark(props) {
    var s = props.size || 28;
    return h('svg', { className: 'w-mark', width: s, height: s, viewBox: '0 0 64 64', 'aria-hidden': 'true' },
      h('path', {
        fillRule: 'evenodd',
        d: 'M8 12h48a4 4 0 0 1 4 4v9a7 7 0 0 0 0 14v9a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4v-9a7 7 0 0 0 0-14v-9a4 4 0 0 1 4-4z' +
          'M26 22.5v19l16-9.5z'
      }));
  }
  function Brand(props) {
    var Tag = props.href ? 'a' : 'span';
    return h(Tag, { className: cx('w-brand', props.size === 'lg' && 'w-brand-lg'), href: props.href, 'aria-label': 'WhatToWatch' },
      h(Mark, { size: props.size === 'lg' ? 44 : 28 }),
      props.markOnly ? null : h('span', { className: 'w-brand-word' }, 'WhatToWatch'));
  }

  /* ---------- Actions ---------- */
  function Button(props) {
    var variant = props.variant || 'secondary';
    var Tag = props.href ? 'a' : 'button';
    var other = rest(props, ['variant', 'size', 'icon', 'iconRight', 'busy', 'busyLabel', 'className', 'children', 'pressed']);
    if (!props.href && !other.type) other.type = 'button';
    if (props.pressed !== undefined) other['aria-pressed'] = props.pressed;
    if (props.busy) other.disabled = true;
    return h(Tag, Object.assign(other, {
      className: cx('w-btn', 'w-btn-' + variant, props.size === 'sm' && 'w-btn-sm', props.className)
    }),
      props.icon ? h(Icon, { name: props.icon, filled: props.iconFilled }) : null,
      h('span', null, props.busy && props.busyLabel ? props.busyLabel : props.children),
      props.iconRight ? h(Icon, { name: props.iconRight }) : null);
  }
  function IconButton(props) {
    var other = rest(props, ['icon', 'label', 'variant', 'className', 'size', 'filled']);
    return h('button', Object.assign({ type: 'button' }, other, {
      className: cx('w-iconbtn', props.variant && 'w-iconbtn-' + props.variant, props.size === 'lg' && 'w-iconbtn-lg', props.className),
      'aria-label': props.label, title: props.label
    }), h(Icon, { name: props.icon, filled: props.filled, size: props.size === 'lg' ? 22 : 18 }));
  }
  function Chip(props) {
    var selectable = props.selected !== undefined;
    var Tag = selectable || props.onClick ? 'button' : 'span';
    return h(Tag, {
      type: Tag === 'button' ? 'button' : undefined,
      className: cx('w-chip', props.selected && 'w-chip-on', props.tone && 'w-chip-' + props.tone),
      'aria-pressed': selectable ? props.selected : undefined,
      onClick: props.onClick
    }, props.selected ? h(Icon, { name: 'check', size: 14 }) : null, props.children);
  }

  /* ---------- Ticket details ---------- */
  function Perforation(props) {
    return h('div', { className: cx('w-perf', props.inset && 'w-perf-inset'), role: 'separator', 'aria-hidden': 'true' },
      h('span', { className: 'w-perf-notch w-perf-l' }), h('span', { className: 'w-perf-line' }), h('span', { className: 'w-perf-notch w-perf-r' }));
  }
  function TicketMeta(props) {
    var parts = [];
    if (props.rating !== undefined) parts.push(props.rating == null ? 'NOT RATED' : 'IMDb ' + Number(props.rating).toFixed(1));
    if (props.year) parts.push(String(props.year));
    if (props.runtime) parts.push(props.runtime + ' MIN');
    (props.extra || []).forEach(function (x) { parts.push(x); });
    return h('span', { className: cx('w-meta', props.className) },
      parts.map(function (p, i) {
        return h(R.Fragment, { key: i }, i ? h('span', { className: 'w-meta-dot', 'aria-hidden': 'true' }, '·') : null,
          h('span', { className: i === 0 && props.rating != null && props.highlight ? 'w-meta-hi' : undefined }, p));
      }));
  }
  function StatusNote(props) {
    var tone = props.tone || 'info';
    var icons = { info: 'info', loading: null, error: 'alert', empty: 'film', success: 'check', invite: 'sparkle' };
    var role = tone === 'error' ? 'alert' : 'status';
    return h('div', { className: cx('w-note', 'w-note-' + tone, props.block && 'w-note-block'), role: role },
      tone === 'loading' ? h('span', { className: 'w-spinner', 'aria-hidden': 'true' }) : h(Icon, { name: icons[tone] }),
      h('div', { className: 'w-note-body' },
        props.title ? h('strong', null, props.title) : null,
        h('span', null, props.children)),
      props.action ? h('div', { className: 'w-note-action' }, props.action) : null);
  }

  /* ---------- Navigation ---------- */
  var NAV = [
    { id: 'home', label: 'Home', href: '/browse' },
    { id: 'search', label: 'Search', href: '/search' },
    { id: 'discover', label: 'Discover', href: '/discover' },
    { id: 'chat', label: 'Chatbot W2W', href: '/chat' },
    { id: 'library', label: 'Library', href: '/library/favorites' }
  ];
  function Navbar(props) {
    var _o = useState(!!props.menuOpen), open = _o[0], setOpen = _o[1];
    var user = props.user;
    return h('header', { className: cx('w-nav', props.scrolled && 'w-nav-filled') },
      h('div', { className: 'w-nav-inner' },
        h(Brand, { href: '/browse' }),
        h('nav', { className: 'w-nav-links', 'aria-label': 'Main navigation' },
          NAV.map(function (l) {
            var on = props.active === l.id;
            return h('a', { key: l.id, href: l.href, className: on ? 'w-on' : undefined, 'aria-current': on ? 'page' : undefined }, l.label);
          })),
        h('div', { className: 'w-nav-end' },
          h('a', { className: 'w-nav-search', href: '/search', 'aria-label': 'Search movies' }, h(Icon, { name: 'search' })),
          user ? h('div', { className: 'w-account' },
            h('button', { type: 'button', className: 'w-account-btn', 'aria-expanded': open, 'aria-haspopup': 'menu', onClick: function () { setOpen(!open); } },
              h('span', { className: 'w-avatar', 'aria-hidden': 'true' }, (user.email || '?').charAt(0).toUpperCase()),
              h('span', { className: 'w-account-mail' }, user.email), h(Icon, { name: 'chevron-down', size: 16 })),
            open ? h('div', { className: 'w-menu', role: 'menu' },
              h('a', { role: 'menuitem', href: '/me/ratings' }, h(Icon, { name: 'star' }), 'My ratings'),
              h('a', { role: 'menuitem', href: '/me/history' }, h(Icon, { name: 'clock' }), 'Watch history'),
              h('a', { role: 'menuitem', href: '/library/lists' }, h(Icon, { name: 'list' }), 'My lists'),
              h('div', { className: 'w-menu-rule' }),
              h('button', { role: 'menuitem', type: 'button', onClick: props.onSignOut }, h(Icon, { name: 'log-out' }), 'Sign out')) : null)
            : h(Button, { variant: 'secondary', size: 'sm', href: '/login', iconRight: 'arrow-up-right' }, 'Sign in'))));
  }
  function Tabs(props) {
    return h('nav', { className: 'w-tabs', 'aria-label': props.label },
      props.items.map(function (t) {
        var on = t.id === props.active;
        return h('a', { key: t.id, href: t.href, className: on ? 'w-on' : undefined, 'aria-current': on ? 'page' : undefined,
          onClick: props.onChange ? function (e) { e.preventDefault(); props.onChange(t.id); } : undefined },
          t.label, t.count != null ? h('span', { className: 'w-tab-count' }, t.count) : null);
      }));
  }
  function Pagination(props) {
    var page = props.page, total = props.totalPages;
    return h('div', { className: 'w-pager' },
      h(Button, { variant: 'secondary', size: 'sm', icon: 'chevron-left', disabled: page <= 1, onClick: function () { props.onChange && props.onChange(page - 1); } }, 'Previous'),
      h('span', { className: 'w-meta' }, 'PAGE ' + page + ' / ' + total),
      h(Button, { variant: 'secondary', size: 'sm', iconRight: 'chevron-right', disabled: page >= total, onClick: function () { props.onChange && props.onChange(page + 1); } }, 'Next'));
  }
  function Footer() {
    return h('footer', { className: 'w-footer' },
      h(Perforation, null),
      h('div', { className: 'w-footer-row' },
        h(Brand, { href: '/browse' }),
        h('p', null, 'Discover your next great story.'),
        h('span', { className: 'w-meta' }, '© ' + new Date().getFullYear() + ' WHATTOWATCH')));
  }

  /* ---------- Movies ---------- */
  function Poster(props) {
    var _f = useState(false), failed = _f[0], setFailed = _f[1];
    var m = props.movie || {};
    if (m.poster && !failed) {
      return h('img', { className: 'w-poster', src: m.poster, alt: '', loading: 'lazy', onError: function () { setFailed(true); } });
    }
    if (m.art) {
      return h('div', { className: 'w-poster w-poster-art', style: { background: m.art[0], color: m.art[1] }, 'aria-hidden': 'true' },
        h('span', { className: 'w-art-shape', style: { borderColor: m.art[1] } }),
        h('span', { className: 'w-art-title' }, m.title),
        h('span', { className: 'w-art-year' }, m.year));
    }
    return h('div', { className: 'w-poster w-poster-empty', 'aria-hidden': 'true' },
      h(Icon, { name: 'play', filled: true, size: 28 }), h('span', null, 'NO POSTER'));
  }
  function LibraryActions(props) {
    var compact = props.compact;
    var signedIn = props.signedIn !== false;
    var _s = useState({ fav: !!props.favorite, later: !!props.watchLater }), st = _s[0], set = _s[1];
    function toggle(k) {
      if (!signedIn) { props.onRequireSignIn && props.onRequireSignIn(); return; }
      var next = Object.assign({}, st); next[k] = !st[k]; set(next);
      props.onChange && props.onChange(k, next[k]);
    }
    return h('div', { className: cx('w-libact', compact && 'w-libact-compact'), onClick: function (e) { e.stopPropagation(); } },
      h('button', { type: 'button', className: cx('w-libbtn', st.fav && 'w-libbtn-fav'), 'aria-pressed': st.fav, disabled: props.busy,
        title: st.fav ? 'Remove from favourites' : 'Add to favourites', 'aria-label': compact ? (st.fav ? 'Remove from favourites' : 'Add to favourites') : undefined,
        onClick: function () { toggle('fav'); } },
        h(Icon, { name: 'heart', filled: st.fav }), compact ? null : h('span', null, st.fav ? 'In favourites' : 'Favourite')),
      h('button', { type: 'button', className: cx('w-libbtn', st.later && 'w-libbtn-later'), 'aria-pressed': st.later, disabled: props.busy,
        title: st.later ? 'Remove from Watch later' : 'Add to Watch later', 'aria-label': compact ? (st.later ? 'Remove from Watch later' : 'Add to Watch later') : undefined,
        onClick: function () { toggle('later'); } },
        h(Icon, { name: st.later ? 'check' : 'plus' }), compact ? null : h('span', null, st.later ? 'Saved for later' : 'Watch later')),
      props.error ? h('span', { className: 'w-error', role: 'alert' }, props.error) : null);
  }
  function AddToList(props) {
    var _o = useState(!!props.open), open = _o[0], setOpen = _o[1];
    var _l = useState(props.lists || []), lists = _l[0], setLists = _l[1];
    var _c = useState(!!props.creating), creating = _c[0], setCreating = _c[1];
    var _n = useState(''), name = _n[0], setName = _n[1];
    var saved = lists.filter(function (l) { return l.checked; }).length;
    if (props.signedIn === false) return h(Button, { variant: 'secondary', icon: 'list', onClick: props.onRequireSignIn }, 'Add to list');
    function flip(id) {
      setLists(lists.map(function (l) {
        if (l.id !== id) return l;
        var on = !l.checked;
        props.onToggle && props.onToggle(id, on);
        return Object.assign({}, l, { checked: on, count: l.count + (on ? 1 : -1) });
      }));
    }
    function create(e) {
      e.preventDefault();
      if (!name.trim()) return;
      var l = { id: 'new-' + Date.now(), name: name.trim(), count: 1, checked: true };
      setLists(lists.concat([l])); setName(''); setCreating(false);
      props.onCreate && props.onCreate(l.name);
    }
    return h('div', { className: 'w-addlist', onClick: function (e) { e.stopPropagation(); } },
      h('button', { type: 'button', className: cx('w-libbtn', saved && 'w-libbtn-listed'), 'aria-haspopup': 'true', 'aria-expanded': open, onClick: function () { setOpen(!open); } },
        h(Icon, { name: 'list' }), h('span', null, saved ? 'In ' + saved + (saved === 1 ? ' list' : ' lists') : 'Add to list'), h(Icon, { name: 'chevron-down', size: 16 })),
      open ? h('div', { className: 'w-addlist-pop', role: 'dialog', 'aria-label': 'Save to a list' },
        h('div', { className: 'w-addlist-head' }, h('span', { className: 'w-eyebrow' }, 'SAVE TO'), h(IconButton, { icon: 'x', label: 'Close', onClick: function () { setOpen(false); } })),
        lists.length ? h('ul', { className: 'w-addlist-items' }, lists.map(function (l) {
          return h('li', { key: l.id },
            h('label', { className: 'w-check-row' },
              h('input', { type: 'checkbox', checked: !!l.checked, disabled: props.busy, onChange: function () { flip(l.id); } }),
              h('span', { className: 'w-check', 'aria-hidden': 'true' }, l.checked ? h(Icon, { name: 'check', size: 14 }) : null),
              h('span', { className: 'w-check-name' }, l.name),
              h('span', { className: 'w-meta w-faint' }, l.count)));
        })) : h('p', { className: 'w-muted w-addlist-empty' }, 'You have no lists yet.'),
        props.error ? h(StatusNote, { tone: 'error' }, props.error) : null,
        h('div', { className: 'w-addlist-foot' },
          creating
            ? h('form', { className: 'w-addlist-new', onSubmit: create },
              h('label', { htmlFor: 'new-list-name', className: 'w-sr' }, 'List name'),
              h('input', { id: 'new-list-name', className: 'w-input', autoFocus: true, maxLength: 60, placeholder: 'New list name', value: name, onChange: function (e) { setName(e.target.value); } }),
              h(Button, { variant: 'primary', size: 'sm', type: 'submit', disabled: !name.trim() }, 'Create'))
            : h('button', { type: 'button', className: 'w-addlist-create', onClick: function () { setCreating(true); } }, h(Icon, { name: 'plus' }), 'New list'))) : null);
  }
  function MovieCard(props) {
    var m = props.movie;
    return h('article', { className: cx('w-card', props.rank && 'w-card-ranked') },
      props.rank ? h('span', { className: 'w-rank', 'aria-label': 'Rank ' + props.rank }, (props.rank < 10 ? '0' : '') + props.rank) : null,
      h('button', { type: 'button', className: 'w-card-poster', onClick: props.onOpen, 'aria-label': 'View details for ' + m.title },
        h(Poster, { movie: m }),
        h('span', { className: 'w-card-veil' }, h('span', null, 'View details'), h(Icon, { name: 'arrow-up-right' }))),
      h('div', { className: 'w-card-info' },
        h('span', { className: 'w-card-title', title: m.title }, m.title),
        h(TicketMeta, { rating: m.rating, year: m.year || 'MOVIE', highlight: true }),
        props.reason ? h('p', { className: 'w-card-reason' }, props.reason) : null,
        props.hideActions ? null : h(LibraryActions, { compact: true, favorite: m.favorite, watchLater: m.watchLater, signedIn: props.signedIn })));
  }
  function SectionHeading(props) {
    return h('div', { className: 'w-sechead', id: props.id },
      props.stamp ? h('span', { className: 'w-stamp' }, props.stamp) : null,
      h('h2', null, props.title),
      h('span', { className: 'w-sechead-rule' }),
      props.count != null ? h('span', { className: 'w-meta' }, props.count) : null);
  }
  function MovieRow(props) {
    var ref = useRef(null);
    var _a = useState({ l: false, r: true }), arrows = _a[0], setArrows = _a[1];
    function update() {
      var el = ref.current; if (!el) return;
      setArrows({ l: el.scrollLeft > 2, r: el.scrollLeft + el.clientWidth < el.scrollWidth - 2 });
    }
    useEffect(function () { update(); window.addEventListener('resize', update); return function () { window.removeEventListener('resize', update); }; }, [props.movies]);
    function move(d) { var el = ref.current; if (el) el.scrollBy({ left: d * Math.max(200, el.clientWidth * 0.85), behavior: 'smooth' }); }
    return h('section', { className: 'w-rowsec', 'aria-label': props.title },
      props.title ? h(SectionHeading, { title: props.title, id: props.id, stamp: props.stamp, count: props.count }) : null,
      props.note ? h('div', { className: 'w-row-note' }, props.note) : null,
      h('div', { className: 'w-row-viewport' },
        arrows.l ? h(IconButton, { icon: 'chevron-left', label: 'Previous movies', variant: 'float', className: 'w-row-prev', onClick: function () { move(-1); } }) : null,
        h('div', { className: 'w-row', ref: ref, onScroll: update },
          props.movies.map(function (m, i) {
            return h(MovieCard, { key: m.id || i, movie: m, reason: props.reasons && props.reasons[i], rank: props.ranked ? i + 1 : undefined, signedIn: props.signedIn });
          })),
        arrows.r ? h(IconButton, { icon: 'chevron-right', label: 'Next movies', variant: 'float', className: 'w-row-next', onClick: function () { move(1); } }) : null));
  }
  function SkeletonRow(props) {
    var n = props.count || 5;
    var items = [];
    for (var i = 0; i < n; i++) items.push(h('div', { key: i, className: 'w-skel-card' }, h('span', { className: 'w-skel w-skel-poster' }), h('span', { className: 'w-skel w-skel-line' }), h('span', { className: 'w-skel w-skel-line w-skel-short' })));
    return h('div', { className: 'w-row w-skel-row', role: 'status', 'aria-label': props.label || 'Loading movies' }, items);
  }
  function Hero(props) {
    var m = props.movie;
    if (!m) {
      return h('section', { className: 'w-hero', 'aria-label': 'Featured movie' },
        h('div', { className: 'w-hero-panel' },
          h('span', { className: 'w-eyebrow' }, 'FEATURED MOVIE'),
          h('h1', { className: 'w-hero-title' }, 'Discover your next story'),
          h('p', { className: 'w-hero-syn' }, 'Find a movie that fits your mood in the WhatToWatch collection.')),
        h('div', { className: 'w-hero-art w-hero-art-empty' }, h(Icon, { name: 'film', size: 40 })));
    }
    return h('section', { className: 'w-hero', 'aria-label': 'Featured movie' },
      h('div', { className: 'w-hero-panel' },
        h('span', { className: 'w-eyebrow' }, h('span', { className: 'w-stamp' }, 'TOP 10'), 'FEATURED MOVIE'),
        h('h1', { className: 'w-hero-title' }, m.title),
        h(TicketMeta, { rating: m.rating, year: m.year, runtime: m.runtime, highlight: true }),
        h('p', { className: 'w-hero-syn' }, m.overview),
        h('div', { className: 'w-hero-actions' },
          h(Button, { variant: 'primary', icon: 'info', onClick: props.onOpen }, 'View details'),
          h(LibraryActions, { favorite: m.favorite, watchLater: m.watchLater, signedIn: props.signedIn }))),
      h('div', { className: cx('w-hero-art', !m.backdrop && 'w-hero-art-poster') },
        m.backdrop ? h('img', { src: m.backdrop, alt: '' }) : h('div', { className: 'w-hero-posterwrap' }, h(Poster, { movie: m })),
        h('span', { className: 'w-hero-index w-meta' }, 'TOP 10 / WHAT TO WATCH')));
  }
  function RatingStars(props) {
    var _r = useState(props.value == null ? null : props.value), val = _r[0], setVal = _r[1];
    var _h = useState(0), hover = _h[0], setHover = _h[1];
    if (props.state === 'loading') return h('div', { className: 'w-rate' }, h('strong', { className: 'w-rate-label' }, 'Your rating'), h(StatusNote, { tone: 'loading' }, 'Loading your rating…'));
    if (props.state === 'signed-out') return h('div', { className: 'w-rate' }, h('strong', { className: 'w-rate-label' }, 'Your rating'),
      h('a', { className: 'w-link', href: '/login' }, 'Sign in to rate this movie'));
    var shown = hover || val || 0;
    return h('div', { className: 'w-rate' },
      h('strong', { className: 'w-rate-label' }, 'Your rating'),
      h('div', { className: 'w-rate-stars', role: 'group', 'aria-label': 'Rate this movie from 1 to 5 stars', onMouseLeave: function () { setHover(0); } },
        [1, 2, 3, 4, 5].map(function (v) {
          return h('button', { key: v, type: 'button', className: cx('w-star', v <= shown && 'w-star-on'), 'aria-label': v + ' stars', 'aria-pressed': val === v,
            disabled: props.busy, onMouseEnter: function () { setHover(v); }, onClick: function () { setVal(v); props.onRate && props.onRate(v); } },
            h(Icon, { name: 'star', filled: v <= shown, size: 20 }));
        })),
      h('span', { className: 'w-rate-status' }, val == null ? 'You have not rated this movie.' : 'You rated this movie ' + val + '/5 stars.'),
      props.error ? h('span', { className: 'w-error', role: 'alert' }, props.error) : null);
  }
  function MovieDetail(props) {
    var m = props.movie;
    var trailer = props.trailer || 'image';
    return h('div', { className: cx('w-modal-wrap', props.inline && 'w-modal-inline') },
      h('div', { className: 'w-scrim', onClick: props.onClose }),
      h('div', { className: 'w-modal', role: 'dialog', 'aria-modal': 'true', 'aria-label': m.title },
        h(IconButton, { icon: 'x', label: 'Close movie details', variant: 'float', className: 'w-modal-close', onClick: props.onClose }),
        h('div', { className: 'w-modal-media' },
          trailer === 'playing' ? h('div', { className: 'w-trailer' }, h(Icon, { name: 'play', filled: true, size: 36 }), h('span', { className: 'w-meta' }, 'YOUTUBE-NOCOOKIE EMBED · AUTOPLAY · MUTED'))
            : m.backdrop ? h('img', { src: m.backdrop, alt: '' })
              : h('div', { className: 'w-modal-fallback', style: m.art ? { background: m.art[0], color: m.art[1] } : undefined }, h('span', null, m.title))),
        h('div', { className: 'w-modal-head' },
          h('h2', { className: 'w-modal-title' }, m.title),
          h(TicketMeta, { rating: m.rating, year: m.year, runtime: m.runtime, highlight: true }),
          h('div', { className: 'w-modal-actions' }, h(LibraryActions, { favorite: m.favorite, watchLater: m.watchLater, signedIn: props.signedIn }),
            props.lists ? h(AddToList, { lists: props.lists, open: props.listsOpen, signedIn: props.signedIn }) : null),
          trailer === 'playing' ? h('p', { className: 'w-hint' }, 'The trailer starts muted. You can turn on sound in the video player.') : null,
          trailer === 'none' || trailer === 'error' ? h(StatusNote, { tone: trailer === 'error' ? 'error' : 'info',
            action: h('a', { className: 'w-link', href: '#', target: '_blank', rel: 'noopener noreferrer' }, 'Search for a trailer on YouTube') },
            trailer === 'error' ? 'Could not load the trailer.' : 'No trailer is available for this movie.') : null),
        h(Perforation, { inset: true }),
        h('div', { className: 'w-modal-body' },
          h('div', { className: 'w-modal-col' },
            h('h3', { className: 'w-eyebrow' }, 'OVERVIEW'),
            h('p', null, m.overview || 'No overview is available for this movie.'),
            h(RatingStars, { value: m.myRating, state: props.signedIn === false ? 'signed-out' : undefined })),
          h('dl', { className: 'w-facts' },
            h('dt', null, 'IMDb'), h('dd', { className: 'w-meta' }, m.rating == null ? 'NOT RATED' : m.rating.toFixed(1) + ' / 10'),
            m.year ? [h('dt', { key: 'a' }, 'Year'), h('dd', { key: 'b', className: 'w-meta' }, m.year)] : null,
            m.runtime ? [h('dt', { key: 'c' }, 'Runtime'), h('dd', { key: 'd', className: 'w-meta' }, m.runtime + ' minutes')] : null,
            m.genres && m.genres.length ? [h('dt', { key: 'e' }, 'Genres'), h('dd', { key: 'f', className: 'w-chips' }, m.genres.map(function (g) { return h(Chip, { key: g }, g); }))] : null,
            h('dt', null, 'Cast'), h('dd', null, m.cast || 'No cast information available.'))),
        h('div', { className: 'w-modal-related' },
          props.similar && props.similar.length
            ? h(MovieRow, { title: 'Similar language and era', movies: props.similar, note: h('span', { className: 'w-muted' }, 'Movies from around the same time with the same original language.') })
            : [h(SectionHeading, { key: 's', title: 'Similar language and era' }), h(StatusNote, { key: 'n', tone: 'empty' }, 'No similar movies found.')])));
  }

  /* ---------- Forms ---------- */
  function TextField(props) {
    var id = props.id || ('f-' + (props.label || '').replace(/\W+/g, '-').toLowerCase());
    var other = rest(props, ['label', 'error', 'hint', 'id', 'className', 'trailing']);
    return h('div', { className: cx('w-field', props.error && 'w-field-invalid', props.className) },
      props.label ? h('label', { htmlFor: id }, props.label) : null,
      h('div', { className: 'w-input-wrap' },
        h('input', Object.assign({ id: id, className: 'w-input', 'aria-invalid': props.error ? 'true' : undefined }, other)),
        props.trailing || null),
      props.error ? h('span', { className: 'w-error', role: 'alert' }, props.error) : props.hint ? h('span', { className: 'w-hint' }, props.hint) : null);
  }
  function SearchForm(props) {
    var _v = useState(props.value || ''), v = _v[0], setV = _v[1];
    return h('form', { className: 'w-search', role: 'search', onSubmit: function (e) { e.preventDefault(); if (v.trim() && props.onSearch) props.onSearch(v.trim()); } },
      h('label', { htmlFor: 'movie-query' }, 'Movie title'),
      h('div', { className: 'w-search-bar' },
        h(Icon, { name: 'search', size: 20 }),
        h('input', { id: 'movie-query', value: v, maxLength: 100, autoComplete: 'off', placeholder: 'For example: The Godfather', onChange: function (e) { setV(e.target.value); } }),
        h(Button, { variant: 'primary', type: 'submit' }, 'Search')));
  }
  function AuthForm(props) {
    var reg = props.mode === 'register';
    return h('form', { className: 'w-auth', onSubmit: function (e) { e.preventDefault(); } },
      h('div', { className: 'w-auth-stub' },
        h('span', { className: 'w-meta' }, reg ? 'ADMIT ONE · NEW MEMBER' : 'ADMIT ONE · MEMBER'),
        h('h2', null, reg ? 'Create an account' : 'Sign in'),
        h('p', null, reg ? 'Start discovering movies you will love.' : 'Welcome back.')),
      h(Perforation, { inset: true }),
      h('div', { className: 'w-auth-body' },
        props.registered ? h(StatusNote, { tone: 'success' }, 'Account created. Please sign in.') : null,
        h(TextField, { label: 'Email', type: 'email', required: true, autoComplete: 'email', placeholder: 'you@example.com', defaultValue: props.email }),
        h(TextField, { label: 'Password', type: 'password', required: true, minLength: 8, placeholder: 'At least 8 characters', autoComplete: reg ? 'new-password' : 'current-password' }),
        reg ? h(TextField, { label: 'Confirm password', type: 'password', required: true, minLength: 8, autoComplete: 'new-password', error: props.mismatch ? 'The passwords do not match.' : undefined }) : null,
        props.error ? h(StatusNote, { tone: 'error' }, props.error) : null,
        h(Button, { variant: 'primary', type: 'submit', className: 'w-btn-block', busy: props.busy, busyLabel: 'Please wait…', iconRight: props.busy ? undefined : 'arrow-up-right' }, reg ? 'Create account' : 'Sign in'),
        h('p', { className: 'w-auth-switch' }, reg ? 'Already have an account? ' : 'New here? ', h('a', { className: 'w-link', href: reg ? '/login' : '/register' }, reg ? 'Sign in' : 'Sign up'))));
  }

  /* ---------- Chat ---------- */
  function ConversationList(props) {
    var items = props.items || [];
    return h('aside', { className: 'w-convos', 'aria-label': 'Conversations' },
      h(Button, { variant: 'primary', icon: 'plus', className: 'w-btn-block', disabled: props.busy, onClick: props.onNew }, 'New conversation'),
      h('h2', { className: 'w-eyebrow' }, 'RECENT'),
      items.length === 0 ? h('p', { className: 'w-muted' }, 'No conversations yet.') : null,
      h('ul', null, items.map(function (c) {
        var on = c.id === props.selected;
        return h('li', { key: c.id, className: on ? 'w-on' : undefined },
          h('button', { type: 'button', className: 'w-convo', 'aria-current': on ? 'true' : undefined, disabled: props.busy, onClick: function () { props.onSelect && props.onSelect(c.id); } },
            h('span', { className: 'w-convo-title' }, c.title), h('span', { className: 'w-meta w-faint' }, c.when)),
          h(IconButton, { icon: 'trash', label: 'Delete conversation ' + c.title, variant: 'danger', disabled: props.busy, onClick: function () { props.onDelete && props.onDelete(c.id); } }));
      })));
  }
  var CHAT_STATUS = {
    no_match: { tone: 'empty', text: 'No movie in the collection matched that. Try a different genre, decade or mood.' },
    insufficient_context: { tone: 'info', text: 'I need a little more to go on. Which movie do you mean, or what are you in the mood for?' },
    error: { tone: 'error', text: 'Something went wrong while writing this reply. Send your message again.' }
  };
  function ChatMessage(props) {
    var user = props.role === 'user';
    var st = !user && props.status && CHAT_STATUS[props.status];
    return h('article', { className: cx('w-msg', user ? 'w-msg-user' : 'w-msg-bot', st && 'w-msg-' + props.status) },
      h('span', { className: 'w-msg-who' }, user ? 'You' : 'WhatToWatch', props.time ? h('span', { className: 'w-meta w-faint' }, props.time) : null),
      props.content ? h('p', null, props.content) : null,
      st ? h(StatusNote, { tone: st.tone }, st.text) : null,
      props.movies && props.movies.length ? h(R.Fragment, null,
        h(Perforation, { inset: true }),
        h('ol', { className: 'w-msg-picks' }, props.movies.map(function (m, i) {
          return h('li', { key: m.id || i },
            h('span', { className: 'w-msg-num w-meta' }, (i < 9 ? '0' : '') + (i + 1)),
            h('div', null, h('a', { className: 'w-link', href: '/movies/' + m.id }, m.title, h(Icon, { name: 'arrow-up-right', size: 14 })), h('span', { className: 'w-muted' }, m.reason)));
        }))) : null);
  }
  function ChatComposer(props) {
    var _d = useState(props.value || ''), d = _d[0], setD = _d[1];
    var locked = props.sending || props.loading;
    return h('form', { className: 'w-composer', onSubmit: function (e) { e.preventDefault(); if (d.trim() && !locked) { props.onSend && props.onSend(d.trim()); setD(''); } } },
      props.suggestions && props.suggestions.length ? h('div', { className: 'w-chips' }, props.suggestions.map(function (s) {
        return h(Chip, { key: s, onClick: function () { setD(s); } }, s);
      })) : null,
      props.error ? h(StatusNote, { tone: 'error' }, props.error) : null,
      h('label', { htmlFor: 'chat-message', className: 'w-sr' }, 'Your message'),
      h('div', { className: 'w-composer-bar' },
        h('input', { id: 'chat-message', value: d, maxLength: 2000, disabled: locked, placeholder: 'What kind of movie would you like to watch?', onChange: function (e) { setD(e.target.value); } }),
        h(Button, { variant: 'primary', type: 'submit', icon: 'send', disabled: !d.trim() || locked }, 'Send')),
      props.sending ? h(StatusNote, { tone: 'loading' }, 'Finding movies and writing a reply…') : null);
  }

  /* ---------- New screens ---------- */
  var LANGS = [['', 'Any language'], ['en', 'English'], ['fr', 'French'], ['ja', 'Japanese'], ['ko', 'Korean'], ['zh', 'Chinese'], ['es', 'Spanish'], ['vi', 'Vietnamese']];
  function RangeFields(props) {
    return h('fieldset', { className: 'w-range' },
      h('legend', null, props.legend),
      h('div', { className: 'w-range-row' },
        h(TextField, { label: 'From', type: 'number', min: props.min, max: props.max, step: props.step, defaultValue: props.from, placeholder: String(props.min) }),
        h('span', { className: 'w-range-dash', 'aria-hidden': 'true' }, '–'),
        h(TextField, { label: 'To', type: 'number', min: props.min, max: props.max, step: props.step, defaultValue: props.to, placeholder: String(props.max) }),
        props.unit ? h('span', { className: 'w-meta w-faint' }, props.unit) : null));
  }
  function FilterPanel(props) {
    var genres = props.genres || [];
    var _g = useState(props.selectedGenres || []), sel = _g[0], setSel = _g[1];
    function flip(id) { setSel(sel.indexOf(id) >= 0 ? sel.filter(function (x) { return x !== id; }) : sel.concat([id])); }
    return h('form', { className: 'w-filters', onSubmit: function (e) { e.preventDefault(); props.onApply && props.onApply(); } },
      h('div', { className: 'w-filters-head' },
        h('h2', null, h(Icon, { name: 'sliders' }), 'Filters'),
        h('button', { type: 'reset', className: 'w-link w-btn-plain', onClick: function () { setSel([]); } }, 'Reset all')),
      h('fieldset', { className: 'w-filter-genres' },
        h('legend', null, 'Genres'),
        h('div', { className: 'w-chips' }, genres.map(function (g) { return h(Chip, { key: g.id, selected: sel.indexOf(g.id) >= 0, onClick: function () { flip(g.id); } }, g.name); }))),
      h(RangeFields, { legend: 'Release year', min: 1920, max: 2026, from: props.yearFrom, to: props.yearTo }),
      h(RangeFields, { legend: 'IMDb rating', min: 0, max: 10, step: 0.1, from: props.minRating, to: props.maxRating, unit: '/ 10' }),
      h(RangeFields, { legend: 'Runtime', min: 0, max: 300, from: props.minRuntime, to: props.maxRuntime, unit: 'MIN' }),
      h('div', { className: 'w-field' },
        h('label', { htmlFor: 'f-lang' }, 'Original language'),
        h('div', { className: 'w-select' },
          h('select', { id: 'f-lang', className: 'w-input', defaultValue: props.language || '' }, LANGS.map(function (l) { return h('option', { key: l[0], value: l[0] }, l[1]); })),
          h(Icon, { name: 'chevron-down', size: 16 }))),
      h(Button, { variant: 'primary', type: 'submit', className: 'w-btn-block' }, sel.length ? 'Show movies (' + sel.length + ' genres)' : 'Show movies'));
  }
  function RatingHistory(props) {
    var items = props.items || [];
    if (!items.length) return h(StatusNote, { tone: 'empty', block: true, title: 'No ratings yet', action: h(Button, { variant: 'secondary', size: 'sm', href: '/browse' }, 'Explore movies') }, 'Rate at least 3 movies you have watched to unlock personalized picks.');
    return h('ul', { className: 'w-ledger' }, items.map(function (r) {
      return h('li', { key: r.id, className: 'w-ledger-row' },
        h('div', { className: 'w-ledger-poster' }, h(Poster, { movie: r.movie })),
        h('div', { className: 'w-ledger-main' },
          h('a', { className: 'w-ledger-title', href: '/movies/' + r.movie.id }, r.movie.title),
          h(TicketMeta, { rating: r.movie.rating, year: r.movie.year })),
        h('div', { className: 'w-ledger-stars', 'aria-label': 'You rated ' + r.rating + ' out of 5' },
          [1, 2, 3, 4, 5].map(function (v) { return h(Icon, { key: v, name: 'star', filled: v <= r.rating, size: 16, className: v <= r.rating ? 'w-star-ink' : 'w-star-off' }); })),
        h('span', { className: 'w-meta w-faint' }, r.date),
        h('div', { className: 'w-ledger-actions' },
          h(IconButton, { icon: 'edit', label: 'Change rating for ' + r.movie.title }),
          h(IconButton, { icon: 'trash', label: 'Remove rating for ' + r.movie.title, variant: 'danger' })));
    }));
  }
  function WatchHistory(props) {
    var groups = props.groups || [];
    if (!groups.length) return h(StatusNote, { tone: 'empty', block: true, title: 'Nothing watched yet' }, 'Movies you open and watch will show up here.');
    return h('div', { className: 'w-history' },
      h('div', { className: 'w-history-bar' },
        h('span', { className: 'w-meta' }, props.total + ' MOVIES WATCHED'),
        h(Button, { variant: 'ghost-danger', size: 'sm', icon: 'trash' }, 'Clear history')),
      groups.map(function (g) {
        return h('section', { key: g.label, className: 'w-history-day' },
          h('h3', { className: 'w-eyebrow' }, g.label),
          h('ul', { className: 'w-ledger' }, g.items.map(function (it) {
            return h('li', { key: it.id, className: 'w-ledger-row' },
              h('span', { className: 'w-meta w-faint w-history-time' }, it.time),
              h('div', { className: 'w-ledger-poster' }, h(Poster, { movie: it.movie })),
              h('div', { className: 'w-ledger-main' },
                h('a', { className: 'w-ledger-title', href: '/movies/' + it.movie.id }, it.movie.title),
                h(TicketMeta, { rating: it.movie.rating, year: it.movie.year, runtime: it.movie.runtime })),
              h('div', { className: 'w-ledger-actions' }, h(IconButton, { icon: 'x', label: 'Remove ' + it.movie.title + ' from history', variant: 'danger' })));
          })));
      }));
  }
  function WatchlistManager(props) {
    var lists = props.lists || [];
    var _s = useState(props.selected || (lists[0] && lists[0].id)), sel = _s[0], setSel = _s[1];
    var _c = useState(!!props.creating), creating = _c[0], setCreating = _c[1];
    var current = lists.filter(function (l) { return l.id === sel; })[0];
    return h('div', { className: 'w-lists' },
      h('aside', { className: 'w-lists-side', 'aria-label': 'Your lists' },
        h('h2', { className: 'w-eyebrow' }, 'YOUR LISTS'),
        h('ul', null, lists.map(function (l) {
          var on = l.id === sel;
          return h('li', { key: l.id },
            h('button', { type: 'button', className: cx('w-list-item', on && 'w-on'), 'aria-current': on ? 'true' : undefined, onClick: function () { setSel(l.id); } },
              h(Icon, { name: l.system ? (l.id === 'favorites' ? 'heart' : 'bookmark') : 'list' }),
              h('span', null, l.name), h('span', { className: 'w-meta w-faint' }, l.count)));
        })),
        creating
          ? h('form', { className: 'w-list-new', onSubmit: function (e) { e.preventDefault(); setCreating(false); } },
            h(TextField, { label: 'List name', placeholder: 'e.g. Sunday classics', maxLength: 60, autoFocus: true }),
            h('div', { className: 'w-row-actions' }, h(Button, { variant: 'primary', size: 'sm', type: 'submit' }, 'Create'), h(Button, { variant: 'ghost', size: 'sm', onClick: function () { setCreating(false); } }, 'Cancel')))
          : h(Button, { variant: 'secondary', icon: 'plus', className: 'w-btn-block', onClick: function () { setCreating(true); } }, 'New list')),
      current ? h('section', { className: 'w-lists-main', 'aria-label': current.name },
        h('div', { className: 'w-lists-head' },
          h('div', null, h('h2', null, current.name), h('span', { className: 'w-meta' }, current.count + ' SAVED MOVIES')),
          current.system ? null : h('div', { className: 'w-row-actions' },
            h(Button, { variant: 'secondary', size: 'sm', icon: 'edit' }, 'Rename'),
            h(Button, { variant: 'ghost-danger', size: 'sm', icon: 'trash' }, 'Delete list'))),
        current.movies && current.movies.length
          ? h('div', { className: 'w-grid' }, current.movies.map(function (m) { return h(MovieCard, { key: m.id, movie: m }); }))
          : h(StatusNote, { tone: 'empty', block: true, title: 'This list is empty', action: h(Button, { variant: 'secondary', size: 'sm', href: '/browse' }, 'Explore movies') }, 'Add movies from any movie card or the detail view.')) : null);
  }

  var WTW = {
    Brand: Brand, Icon: Icon, Button: Button, IconButton: IconButton, Chip: Chip, Perforation: Perforation, TicketMeta: TicketMeta,
    StatusNote: StatusNote, Navbar: Navbar, Tabs: Tabs, Pagination: Pagination, Footer: Footer, Poster: Poster, MovieCard: MovieCard,
    SectionHeading: SectionHeading, MovieRow: MovieRow, SkeletonRow: SkeletonRow, Hero: Hero, LibraryActions: LibraryActions, AddToList: AddToList,
    RatingStars: RatingStars, MovieDetail: MovieDetail, TextField: TextField, SearchForm: SearchForm, AuthForm: AuthForm,
    ConversationList: ConversationList, ChatMessage: ChatMessage, ChatComposer: ChatComposer, FilterPanel: FilterPanel,
    RatingHistory: RatingHistory, WatchHistory: WatchHistory, WatchlistManager: WatchlistManager
  };
  window.WTW = Object.assign(window.WTW || {}, WTW);
})();
