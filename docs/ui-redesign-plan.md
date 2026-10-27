# Kế hoạch re-skin frontend WhatToWatch (Phase 0: Recon)

## Bối cảnh
Re-skin tại chỗ `frontend/` theo thiết kế "Ticket Stub" trong `docs/design/whattowatch-design/project/` (lưu ý: thư mục thật là `whattowatch-design`, không phải `whattowatch`). Giữ nguyên route, API proxy, tên event. Không đụng backend/AI/Docker/CI.
Tài liệu Phase 0, chờ duyệt trước khi viết code giao diện.

## Phát hiện từ recon
- Stack khớp quyết định: Next **11.0.1** Pages Router, **React 17** (bundle tham chiếu dùng React 18, không ảnh hưởng vì ta chỉ port markup/CSS), `sass`, SCSS modules, TypeScript 4.3.5 strict. → Không cần dừng lại.
- Hiện dùng `react-icons`, `framer-motion`, `swiper`, `axios`, `react-device-detect`. Chỉ thêm `lucide-react` (cần chọn bản hỗ trợ React 17 + TS 4.3.5, sẽ kiểm tra khi cài).
- Frontend nhỏ (~2.5k dòng): `pages/` (index, login, register, browse, search, chat, library/[kind], movies/[id], api/*), `components/` (Banner, List, Modal, Navbar, LibraryActions, MovieRating, Recommendations, WhatToWatch/AuthForm, Layout, Button, Brand, Footer), `styles/*.module.scss`, `lib/*` (backend, movies, chat, library, recommendations).
- `_app.tsx` render `<Browse/>` phía sau khi vào `/movies/[id]` (modal route) — giữ cơ chế này.
- Có code thừa từ starter (`utils/apiResolvers.ts`, `pages/api/discover.ts` dùng TMDB, `popular`, `trending`, `utils/icons.ts`, `SearchBar.tsx`) — `/api/discover` hiện KHÔNG phải proxy `GET /movies/filter`; sẽ cần thay ở Phase 5.
- Navbar hiện: Home, Search, Chatbot W2W, Favourite, Watch later + nút Sign in/out; thiết kế: Home, Search, Discover, Chatbot W2W, Library + account menu.
- `/api/auth/session` chỉ trả `authenticated` → lấy email bằng cách đọc `sub` từ JWT cookie phía server route (cookie `wtw_session`), ghi vào `docs/backend-requests.md`.

## a) Bảng component thiết kế → file hiện có
| Thiết kế | File hiện có / đề xuất |
|---|---|
| Icon, IconButton, Chip, Perforation, TicketMeta, StatusNote, SectionHeading, SkeletonRow, Tabs, TextField | **Mới** `components/ui/*` |
| Button | `components/Button` (viết lại: variant primary/secondary/ghost/ghost-danger, `href`, `busy`) |
| Brand | `components/Brand` (dùng `wtw-mark.svg` + wordmark Newsreader) |
| Poster | **Mới** (fallback `/assets/poster-placeholder.svg`), thay `<img>` rải rác |
| Navbar (+account menu) | `components/Navbar/{index,Menu,Profile}` (bỏ `SearchBar.tsx` nếu không dùng) |
| Footer | `components/Footer` |
| Hero | `components/Banner` |
| MovieRow / MovieCard / rank Top 10 | `components/List/{index,MovieRow,MovieCard}` |
| LibraryActions | `components/LibraryActions` |
| RatingStars | `components/MovieRating` |
| MovieDetail (modal) | `components/Modal` |
| For you (6 trạng thái) | `components/Recommendations` |
| LandingScreen | `pages/index.tsx` |
| AuthForm | `components/WhatToWatch/AuthForm` |
| SearchForm, Pagination | `pages/search.tsx` (tách `components/ui/Pagination`) |
| ChatScreen, ConversationList, ChatMessage, ChatComposer | `pages/chat.tsx` (tách 3 component, **mới**) |
| LibraryScreen / Tabs | `pages/library/[kind].tsx` |
| RatingHistory, WatchHistory | **Mới** `pages/me/ratings.tsx`, `pages/me/history.tsx` |
| FilterPanel, DiscoverScreen | **Mới** `pages/discover.tsx` |
| WatchlistManager, AddToList | **Mới** (`library/lists`, popover trong Modal) |

## b) Bảng màn hình → trạng thái
| Màn hình | Trạng thái | Việc cần làm |
|---|---|---|
| Landing `/` | Done | Layout mới |
| Sign in / Sign up | Done | Layout mới + stub vé (Perforation) |
| Browse | Done (+Frontend) | Hero split, rank Top 10, nút Favourite/Watch later trên hero |
| Search | Done (+Frontend) | Link "Try Discover", "Ask Chatbot W2W" khi no match |
| Movie detail modal | Done (+Frontend) | Chip thể loại (DTO chưa có genres → ẩn/ghi chú) |
| Chat | Done (+Frontend) | Hiển thị theo status, chip gợi ý, timestamp; không đổi chat API. Hội thoại mở lại mất `status` (backend) |
| My ratings | Frontend | Page + proxy `GET /ratings/my-ratings` + `DELETE`; thiếu year/IMDb trong response |
| Watch history | Frontend | Page + proxy + gọi `POST /watch-history` khi mở phim; `posterPath` thô → tự dựng URL |
| Account menu | Frontend | Đọc JWT `sub` |
| Discover | Backend-blocked (có fix) | Filter so `tmdbVoteAverage` nhưng card hiển thị `imdbRating` → kết quả sai |
| My lists | Backend-blocked | `/watchlists/lists` trả cả Default Watchlist, DELETE xoá được nó, lỗi Optional khi ≥2 list |
| Add to list | Backend-blocked | Không có endpoint "phim này nằm ở list nào" |

## c) Cấu trúc token SCSS & thư mục
- `styles/_tokens.scss` (nguồn duy nhất): biến SCSS (`$surface-000`, `$space-4`, `$radius-sm`…) + `:root { --surface-000: …}` sinh từ cùng map; mixin typography (`display-xl`, `title-m`, `meta`, `rank`…), `focus-ring`, `reduced-motion`. Thay `_variables.scss`, dọn `_mixins.scss`.
- `styles/globals.scss`: reset, font, nền `surface-000`, focus-visible 2px `focus`, `prefers-reduced-motion`.
- Font: Newsreader / Be Vietnam Pro / JetBrains Mono qua `<link>` Google Fonts trong `_document.tsx`.
- Thư mục: `components/ui/` (primitive: Icon, Button, IconButton, Chip, Perforation, TicketMeta, StatusNote, Poster, Tabs, Pagination, SectionHeading, SkeletonRow, TextField) kèm `*.module.scss` cạnh file; component theo tính năng giữ chỗ cũ; `components/chat/*`, `components/me/*`, `components/discover/*` cho phần mới.
- Assets: chép `wtw-mark.svg`, `favicon.svg`, `poster-placeholder.svg` vào `public/`.
- Không gradient, không emoji; dark only.

## d) Mốc (milestone) & commit
1. **Phase 1 Nền tảng**: tokens, font, globals, cài `lucide-react` + `Icon`, Brand, Button, IconButton, Chip, Perforation, TicketMeta, StatusNote, Poster, Footer, Navbar + account menu.
2. **Phase 2**: Landing, Auth, Browse (Hero/Row/Card/Rank/For you 6 state), Search+Pagination, Modal (RatingStars, trailer, similar).
3. **Phase 3**: Chat + status/chip/timestamp.
4. **Phase 4**: My ratings, Watch history (+proxy, DELETE, POST watch-history).
5. **Phase 5**: Discover, My lists, Add to list (ẩn/disable phần chưa chạy) + `docs/backend-requests.md`.
Mỗi phase: lint, type-check (`tsc --noEmit`), build, chạy dev, so sánh PNG 1520px; commit riêng; dừng chờ duyệt. Nếu không xác minh được bằng mắt thì nói rõ.

## e) Câu hỏi cho bạn
1. **Gỡ `react-icons`/`framer-motion`/`swiper`** sau khi không còn dùng? (đề xuất: gỡ react-icons ở cuối Phase 2; framer-motion/swiper chỉ gỡ nếu hết dùng; "không thêm dependency" không cấm gỡ.)
2. **Code thừa từ starter** (`pages/api/discover.ts` TMDB, `popular`, `trending`, `utils/apiResolvers.ts`, `SearchBar.tsx`): xoá hay để nguyên? Đề xuất thay `/api/discover` bằng proxy `/movies/filter` ở Phase 5, còn lại xoá khi chắc chắn không dùng.
3. **lucide-react + React 17/TS 4.3.5**: chấp nhận ghim phiên bản cũ tương thích (nếu bản mới lỗi type)?
4. **Email account menu** bằng decode JWT `sub` trong API route `/api/auth/session` (thêm field `email`): OK?
5. **Discover** trước khi backend sửa: ship page ẩn khỏi Navbar hay hiện nhưng ghi chú cảnh báo? (đề xuất: ẩn link + banner "đang chờ backend" nếu truy cập trực tiếp.)
6. Nav "Favourite / Watch later" hiện có sẽ gộp vào "Library" (tab) theo thiết kế — xác nhận.

## Xác minh (sau mỗi phase)
`cd frontend && npm run lint && npx tsc --noEmit && npm run build`, `npm run test:contract`, `npm run dev` rồi so từng màn ở 1520px với `assets/UI/*.png`.
