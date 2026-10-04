# Bàn giao catalog IMDb–TMDB cho MySQL và Qdrant

## Trạng thái cuối — đã dừng và đóng gói bàn giao

Theo yêu cầu mới nhất, đã chạy thêm một batch nhỏ rồi dừng có kiểm soát:
**11.347 phim sạch, 17 failed, 8 unmatched, 204.037 pending** trong tổng 215.409.
Đã khôi phục DNS hotspot về auto-DNS, DNS thực tế `172.20.10.1`.
Lưu lượng đợt 6 GB ghi nhận lúc dừng: **137.982.601 bytes**.
Không còn tiếp tục mục tiêu 20.000 phim trên máy này.

Gói gửi: `data/processed/handoff/catalog_handoff.zip` (đã đóng gói lại cho mục tiêu 100.000 phim sạch), kèm
SHA-256 trong `catalog_handoff.sha256`. Gói có checkpoint SQLite, raw cache,
script làm sạch/xuất/validation, `START.py`, `START.sh`, requirements tối thiểu
và hướng dẫn tiếng Việt. Không có `.env`, API key hay log.
Người nhận chạy **`bash START.sh`** hoặc **`py START.py`** trên Windows để tiếp tục
đến đủ 100.000 phim sạch tổng cộng (gồm 11.347 phim đã có), nhập API key riêng; không áp dụng hạn mức hotspot của máy gửi.
Hướng dẫn nguồn: `docs/catalog_handoff_vi.md`.

Kiểm chứng: 20 tests đạt, Bash syntax đạt; đã kiểm tra SHA-256 mọi file trong ZIP,
giải nén sang thư mục tạm độc lập rồi chạy `START.py --offline`: xuất 11.347 phim,
validation subset đạt và JSONL byte-identical với bản gốc. Chưa chạy online hoặc
kiểm tra trực tiếp trên Windows ở máy người nhận. Full catalog chưa hoàn tất.

Đã dọn snapshot dry-run, báo cáo/log trung gian, sample đã thay thế, CSV lọc cũ
và JSONL nguồn có thể xuất lại từ SQLite. Giữ file sạch, checkpoint/cache,
report cuối, query evaluation và lịch sử ngân sách. Báo cáo dọn dẹp:
`docs/evidence/week-03/catalog_cleanup.json`. Lịch sử hạn mức 500 MB chuyển sang
`data/processed/network_history/`; không chạy lại lệnh 500 MB cũ để tạo ngân sách mới.
Các đường dẫn snapshot/log đã xóa trong phần dưới chỉ còn là lịch sử.

## Phạm vi hiện tại — lấy trước 20.000 phim

Sau khi mất kết nối, người dùng yêu cầu tiếp tục nhưng giảm mục tiêu xuống
**20.000 phim thành công tổng cộng**, thay thế mục tiêu một nửa catalog.
Checkpoint lúc kiểm tra: **4.968 succeeded, 7 unmatched, 9 failed**; còn cần
15.032 phim thành công để đạt mục tiêu mới. Runner đã tự dừng với
`active_connection_changed`, xuất snapshot 4.968 phim và khôi phục cấu hình DNS.
Dung lượng ghi nhận lúc dừng là 56.737.186 bytes; giữ nguyên state 6 GB khi resume.

Dùng lệnh ở mục dưới với `--target-successes 20000` thay cho `107705`.
Vẫn ưu tiên IMDb votes giảm dần. Phần còn lại để đợt sau; không còn mô tả
20.000 phim là một nửa catalog. Validator của đợt này ghi
`data/processed/hotspot_20k_validation.json` và `hotspot_20k_validation.log`.

## Phạm vi mới nhất — chỉ thu thập một nửa catalog

Người dùng thu hẹp yêu cầu: **107.705 phim accepted tổng cộng**, khoảng một nửa
215.409 phim eligible; **còn khoảng một nửa để thu thập trong đợt sau**.
Đây là mục tiêu, chưa phải số đã hoàn thành. Vẫn ưu tiên IMDb votes giảm dần
và giữ trần 6 GB hiện có; nếu hết dung lượng trước thì báo số thực tế.

Đã dừng runner cũ có kiểm soát, khôi phục DNS và kiểm tra snapshot:
**2.889 accepted**, validation subset đạt, 0 lỗi validation. 20 tests offline đạt,
gồm kiểm tra target tính cả checkpoint, bỏ qua unmatched và không tải thêm khi
đã đạt target. Còn cần thêm 104.816 accepted để đạt mục tiêu tại mốc này.

Lệnh tiếp tục (giữ nguyên file usage để không reset dung lượng):

```bash
python3 -u data/scripts/run_metered_catalog.py --max-mb 6000 \
  --connection 23cf9d71-8dec-4dad-94e9-787093347bc6 --device wlo1 \
  --usage data/processed/hotspot_6gb_usage.json --output data/processed \
  --rate 2 --target-successes 107705
```

Khi dừng, `data/processed/catalog_scope.json` ghi mục tiêu, số accepted thực tế,
target_reached và số chưa accepted; `complete=false` vẫn giữ cho catalog một phần.
Log tiếp tục append vào `hotspot_6gb_run.log`; validation sau lượt chạy mới ghi
`hotspot_half_validation.json` và `hotspot_half_validation.log`.
Các mục dưới giữ lịch sử yêu cầu trước khi thu hẹp phạm vi.

## Tiếp tục ngày 28/09/2026 — hotspot Lewis, hạn mức mới 6 GB

Người dùng xác nhận đã chuyển về Lewis và cho phép tải toàn bộ catalog trong
hạn mức mới **6 GB (6.000.000.000 bytes)**. Đã xác minh connection UUID
`23cf9d71-8dec-4dad-94e9-787093347bc6`, probe TMDB thành công và chạy tiếp
checkpoint với tốc độ tối đa 2 request/giây. 25 phim đầu của đợt mới đều thành
công; lúc đó còn 213.817 records pending. Đây là tiến độ, chưa phải kết quả cuối.
19 tests offline đạt trước khi chạy.

Đợt mới dùng `data/processed/hotspot_6gb_usage.json`; giữ nguyên lịch sử hạn mức
500 MB cũ. Việc tạo ngân sách mới dựa trên xác nhận 6 GB của người dùng sau khi
đổi mạng/reset bộ đếm. Không xóa/reset state 6 GB khi resume đợt này.
Dung lượng được tính bằng RX+TX của interface, bao gồm ứng dụng khác trên máy;
không đo được lưu lượng dùng trực tiếp trên điện thoại. Dừng trước trần 5 MB.

Log chạy: `data/processed/hotspot_6gb_run.log`. Khi dừng, runner khôi phục
auto-DNS hotspot, xuất JSONL và `movies_cleaned_full_report.json`. Đã xếp hàng
validator offline bằng khóa `catalog.lock`; kết quả sẽ nằm ở
`data/processed/hotspot_6gb_validation.json` và `.log`. Validation mặc định có
scope subset; phải đối chiếu pending/rejected trong report trước khi kết luận
catalog hoàn tất. Các phần dưới là lịch sử của những đợt trước.

## Đợt chạy có hạn mức 500 MB

Người dùng chọn tiếp tục hotspot với tối đa **500 MB**, và chấp nhận catalog 1/4
hoặc 1/2 nếu không thể lấy full. Chưa xác nhận đạt các mức đó: 1/4 eligible catalog
là 53.853 records, 1/2 là 107.705 records; số accepted phải báo riêng với processed.
Để catalog một phần hữu ích hơn, các lượt tiếp theo ưu tiên số IMDb votes giảm dần,
hòa vote sắp theo IMDb ID. Cache/phim đã hoàn thành trước đó vẫn giữ nguyên.

`run_metered_catalog.py` quản lý DNS hotspot và khôi phục trong finally, kể cả
SIGTERM có kiểm soát; xuất snapshot khi dừng. Giới hạn dựa trên tổng RX+TX interface,
dừng trước 500 MB với vùng đệm 5 MB, kiểm tra mỗi request và mỗi chunk 16 KiB;
không kiểm soát được cước nhà mạng hoặc lưu lượng trực tiếp của điện thoại/thiết bị
khác. Đếm response đã giải nén riêng để tham khảo, không nhầm với byte truyền mạng.
Nếu đổi kết nối hoặc reset counter thì dừng, không tự xóa ngân sách.

State dung lượng tích lũy: `data/processed/hotspot_500mb_usage.json`.
DNS gốc: `data/processed/hotspot_500mb_usage.dns.json`.
Chạy lại cùng lệnh dùng lại ngân sách, kể cả lưu lượng interface kể từ lần kiểm tra
cuối; không đổi tên/xóa file usage để lách hạn mức đã được người dùng chọn.

```bash
python3 -u data/scripts/run_metered_catalog.py --max-mb 500 \
  --connection 23cf9d71-8dec-4dad-94e9-787093347bc6 --device wlo1 \
  --usage data/processed/hotspot_500mb_usage.json --output data/processed --rate 2
```

19 tests offline đạt, gồm budget persistence, dừng giữa response, không đánh dấu
phim pending thành failed khi hết ngân sách và không gửi request nếu đổi mạng.
Snapshot giữa chừng 576 phim đã được validation thành công. Kết quả cuối của đợt
500 MB cần đọc report/checkpoint thực tế sau khi process dừng; chưa có full dataset.

## Trạng thái hiện tại — hotspot và dry run thực tế

Hotspot `Lewis` truy cập TMDB thành công. Đã chạy 3 phim tham chiếu, rồi mở rộng
thành 25 phim: **24 succeeded, 1 unmatched (`tt0000886`), 0 failed**.
Full catalog còn **215.384 phim chưa xử lý**; chưa tạo dataset full để import.
37 request (gồm probe) nhận 599.183 bytes response body **sau giải nén**;
đây không phải số byte nhà mạng tính, không đủ để kết luận 1 GB đáp ứng full run.
Mẫu này thiên về phim cũ ở nhóm ít votes nên cũng không đại diện toàn catalog.
Không tải file ảnh/video. Đợt API đã dừng ngay sau dry run, khôi phục và xác minh
auto-DNS IPv4/IPv6 cùng DNS hotspot `172.20.10.1`, `fe80::34b1:ebff:feb8:2664`.
Không dùng cấu hình DNS Wi-Fi cũ để ghi đè DNS hotspot.

Output thực tế nằm trong `data/processed/dry_run_25/` (tên file có `full` là
convention của exporter, **chỉ chứa sample**, report có `complete=false`):

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| imdb_tmdb_full.jsonl | 304086 | 4d7dd0b84ce472c8386081b8c49308622b7d9e91b712ffe6ced2f16442bbe282 |
| movies_cleaned_full.jsonl | 137434 | d23e701e53a3802788b450016215361e302d38ce042763cd2ee27103b023bd2c |
| movies_cleaned_full_rejected.jsonl | 0 | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| movies_cleaned_full_unmatched.jsonl | 58 | 244fa4c96d87b84df6c6bec6df2499a52902c7a63b5d3406c86c483fd567f572 |

Validation streaming đạt cho 24 dòng (`validation.json`, scope=subset).
Rerun bỏ qua đủ 25 checkpoint, byte output không đổi. Replay trên bản sao SQLite
tạm (không xóa checkpoint thật), chia 7 rồi 18 records: cache hit cả 25 records,
0 request, output byte-identical. Bằng chứng: `resume_evidence.json`.
Raw cache được giữ lại trong `data/processed/tmdb_cache/` để full run tái sử dụng.

Thiếu trên 24 phim accepted: overview 0%, poster 12,5%, backdrop 41,67%,
keywords 16,67%, cast 4,17%, director 0%, trailer 41,67%, country 0%, language 0%.
Đây là tỷ lệ sample, không phải tỷ lệ full catalog; mapping sample đạt 24/25=96%.

Đã đọc và kiểm tra thủ công 20 phim reservoir trong validation report: tiêu đề,
ID, năm IMDb, overview, director, language và missing fields. Không phát hiện
ghép sai từ các trường đã kiểm tra; validator xác minh external ID từng phim.
Giữ các khác biệt nguồn: phim câm có language `xx`; `The Last Bohemian` có năm
IMDb 1913 trong khi overview TMDB nhắc 1912; không tự sửa năm để khớp văn bản.
Đây là review sample, không thay review/validation full khi dataset hoàn tất.

Ba phim The Godfather, Fight Club, Interstellar khớp IMDb/TMDB ID, top-5 cast và
embedding_text của sample committed. Live API trả full cast (81/76/35 người),
sample cũ chỉ có 10 người; popularity/rating có thay đổi, trailer chọn deterministic
có thể khác. Schema không đổi và không cắt mất cast để ép bằng sample cũ.

Phần tiếp theo: thống nhất đường truyền/hạn mức phù hợp trước full run trên 215.384
records còn lại. Không tự tiêu hết gói hotspot 1 GB. Các mục sau lưu lịch sử chuẩn bị
và hướng dẫn; mục trạng thái này là kết quả mới nhất.

## Cập nhật lần thử kết nối

Người dùng đã yêu cầu agent trực tiếp đổi DNS và khôi phục sau khi xong.
Đã đổi Wi-Fi `wlo1` sang `1.1.1.1`, `1.0.0.1` và xác minh bằng resolvectl.
Chạy lệnh dry run 25 phim: bước probe `/3/configuration` (một attempt, không retry)
thất bại với `network_retries_exhausted`; chưa chạy request lấy metadata phim.
Đã lập tức khôi phục cả cấu hình IPv4/IPv6 auto-DNS ban đầu và xác minh DNS thực tế
trở lại `192.168.0.1`, domain `www.tendawifi.com`. Không cần nhập mật khẩu.
Chưa xác định nguyên nhân lỗi mạng; đổi DNS Cloudflare chưa giải quyết được kết nối.
Lần chẩn đoán có giới hạn tiếp theo (được người dùng cho phép tiếp tục tự xử lý)
ghi nhận chuỗi `ConnectionError → ProtocolError → ConnectionResetError`, errno 104,
trước phản hồi HTTP. Không có proxy HTTP/HTTPS/ALL_PROXY trong môi trường lệnh.
Không in exception message/URL để tránh lộ API key. Đã dừng ngay sau probe và
khôi phục DNS; lần kiểm tra sau reapply xác nhận cả NetworkManager và resolvectl
đều trở lại `192.168.0.1`, domain `www.tendawifi.com`, auto-DNS IPv4/IPv6 bật.
Pipeline hiện phân loại lỗi DNS/TLS/reset an toàn; **15 tests offline đạt**.
Cần kết nối mạng tới TMDB hoạt động (ví dụ thử hotspot do người dùng cung cấp)
trước khi tiếp tục; chưa xác định thiết bị hoặc hệ thống nào đã reset kết nối.
Các số liệu offline dưới đây giữ nguyên; những câu “chưa gửi request” bên dưới
mô tả mốc trước lần probe này. Full dataset vẫn chưa hoàn thành.

Trạng thái: **chưa có full dataset để import**. Kiểm kê offline và dry run cleaning
3 phim đã xong; đang chờ xác nhận đổi DNS trước request TMDB đầu tiên. Chưa chạy
dry run 25 phim thật, full ingestion hoặc validation full. Không dùng các fixture
giả lập trong tests làm dữ liệu phim thật.

## Nguồn và kết quả kiểm kê

Đếm lại trực tiếp gzip IMDb và MovieLens local, không suy ra từ tên file:

| Chỉ tiêu | Số dòng |
| --- | ---: |
| IMDb title.basics | 12.788.670 |
| movie | 756.837 |
| tvMovie | 156.126 |
| movie/tvMovie có numVotes >= 50 | 215.409 |
| MovieLens links.csv | 87.585 |
| Eligible có mapping không xung đột | 75.713 |
| Eligible cần /find | 139.696 |
| Eligible có mapping MovieLens xung đột (đã loại khỏi mapping tin cậy) | 36 |
| Cache raw TMDB đầy đủ | 0 |
| Sample metadata đã chuẩn hóa | 3 |

`movies_filtered_step1.csv` có đúng 215.409 phim eligible, không thiếu ID so với
catalog mới. Có một khác biệt do pandas trước đây đọc title `None` của
`tt37879948` thành ô rỗng; catalog SQLite giữ nguyên title IMDb. Sample ba phim
The Godfather (238), Fight Club (550), Interstellar (157336) khớp mapping MovieLens.

File raw hiện có: `title.basics.tsv.gz`, `title.ratings.tsv.gz`,
`title.crew.tsv.gz`, `title.principals.tsv.gz`, `title.akas.tsv.gz`,
`name.basics.tsv.gz`, `links.csv`, tất cả trong `data/raw/`.
Catalog này chỉ cần basics, ratings và links; không tải lại các dump đã có.
`data/processed/catalog_inventory.json` ghi thời gian kiểm kê, kích thước và SHA-256
ba nguồn sử dụng. `data/processed/catalog.sqlite` giữ eligible IMDb và mapping.

Các file trước đây: `movies_cleaned.jsonl` có 3 dòng, `movies_cleaned_rejected.jsonl`
có 0 dòng, `unmatched_step3.csv` có 1 dòng, `evaluation_query_set_v0.csv` có 6 dòng.
Không có cache raw từ script mapping/explore trước đây; cả hai script đó gọi API
ngay ở top level và không có resume. Không chạy chúng để tạo full catalog.

## Pipeline và tái tạo

```bash
# Offline, chỉ tạo database mới; từ chối ghi đè database/checkpoint đã tồn tại.
python3 data/scripts/catalog_inventory.py
python3 -m pytest data/tests -q

# Offline: không có cache thì ghi nhận pending, không coi là unmatched.
python3 data/scripts/full_catalog.py --limit 3
```

`full_catalog.py` dùng SQLite transaction cho từng phim và unique index cho TMDB ID
đã thành công. Raw JSON cache nằm tại `data/processed/tmdb_cache/{find,movie}/`;
ghi file tạm, fsync rồi rename trước transform. Crash sau khi lưu raw nhưng trước
checkpoint sẽ đọc lại cache. Kết quả JSONL được xuất theo luồng từ checkpoint,
không append nên chạy lại không sinh dòng trùng. Khóa file ngăn hai writer cùng DB.
IMDb và TMDB external ID phải khớp; response thiếu cấu trúc credits/keywords/videos
bị giữ lại để kiểm tra, không được coi là cache hợp lệ.

Chỉ sau khi người dùng xác nhận “đã đổi DNS”, chạy dry run 25 phim đã chọn
(3 phim sample, 12 phim 50–100 votes, 10 phim trên 100.000 votes):

```bash
python3 data/scripts/full_catalog.py --dns-confirmed --rate 2 \
  --ids data/processed/dry_run_25_ids.txt --output data/processed/dry_run_25
```

Sau khi dry run thực tế và các kiểm tra bắt buộc đạt, dùng batch có checkpoint:

```bash
python3 data/scripts/full_catalog.py --dns-confirmed --rate 2 --limit 1000
# Resume: lặp lại cùng lệnh; bỏ qua succeeded/unmatched/failed đã checkpoint.
# Chỉ retry failed đã ghi riêng, không gọi lại succeeded:
python3 data/scripts/full_catalog.py --dns-confirmed --rate 2 --limit 1000 --retry-failed
# Xuất snapshot offline từ checkpoint hiện có:
python3 data/scripts/full_catalog.py --limit 1 --output data/processed
```

Snapshot chưa hoàn tất có `complete=false`, `pending_rows`/`rejected_rows` và
`run_completed_at=null`. Cần validation đầy đủ trước khi bàn giao; cờ complete
chỉ phản ánh ingestion đã xử lý hết, không thay thế validation.
Credential đọc từ `TMDB_API` qua environment/.env, không ghi key hoặc exception URL.
Giới hạn mặc định 2 request/giây; tối đa 4 attempts, exponential backoff, tôn trọng
Retry-After. Delay trên 60 giây hoặc lỗi mạng lặp lại sẽ dừng batch để báo đổi DNS lại.

Endpoint dự kiến: một `GET /3/configuration` kiểm tra kết nối không retry;
`GET /3/find/{imdb_id}?external_source=imdb_id`; và
`GET /3/movie/{tmdb_id}?append_to_response=credits,keywords,videos&language=en-US`.
[TMDB hỗ trợ append_to_response](https://developer.themoviedb.org/docs/append-to-response)
để gộp tài nguyên phụ vào request detail.
Trần kế hoạch ban đầu: 139.696 find + tối đa 215.409 detail = 355.105 request,
cộng một probe mỗi lần chạy online và retry nếu có. Find không có kết quả sẽ giảm
số detail. Ở 2 req/s tương đương tối đa khoảng 49,32 giờ lý thuyết, chưa tính
độ trễ/backoff. Chưa đo tốc độ thực tế. Chưa gửi request nào tới api.themoviedb.org.

## Output dự kiến và mapping MySQL

File Khánh Vũ dùng để import sau validation:
`data/processed/movies_cleaned_full.jsonl`.
Các file kèm theo: `imdb_tmdb_full.jsonl`, `movies_cleaned_full_report.json`,
`movies_cleaned_full_rejected.jsonl`, `movies_cleaned_full_unmatched.jsonl` trong
`data/processed/`. Hiện chưa tạo các file full này.

Backend hiện chưa có entity/migration catalog; mapping dưới đây là contract bàn giao
theo AGENT.md, không phải xác nhận các bảng đã được triển khai.

| JSONL | MySQL đích / quy tắc |
| --- | --- |
| movie_id | `movies.id` do MySQL cấp; đầu vào null |
| imdb_id, tmdb_id | `movies.imdb_id`, `movies.tmdb_id`, unique |
| title, original_title, overview, tagline | Cột cùng tên trong `movies` |
| release_date, runtime_minutes, original_language, adult | Cột cùng tên trong `movies`; giữ null |
| imdb_rating, imdb_vote_count, tmdb_vote_average, tmdb_popularity | Cột cùng tên trong `movies` |
| status, poster_path, backdrop_path | Cột cùng tên trong `movies` |
| trailer.key/site/type | `movies.trailer_key/trailer_site/trailer_type`; null nếu không có |
| trailer.official | Metadata bổ sung; cần migration nếu muốn lưu |
| genres[].tmdb_id/name | Upsert `genres`, liên kết `movie_genres` |
| keywords[].tmdb_id/name | Upsert `keywords`, liên kết `movie_keywords` |
| cast[].tmdb_id/name | Upsert `people` bằng TMDB person ID |
| cast[].character/order | `movie_cast` với movie FK và person FK; giữ credit order |
| directors[].tmdb_id/name | Upsert `people` bằng TMDB person ID |
| directors[].job | `movie_crew`, job=`Director`, movie FK và person FK |
| production_countries | Giữ ISO code và name; cần Khánh Vũ bổ sung nơi lưu (JSON hoặc bảng quan hệ), schema hiện chưa định nghĩa |
| imdb_year, imdb_title, imdb_genres | Metadata nguồn; cần cột bổ sung nếu lưu, không nhầm imdb_year với năm release_date |
| missing_fields, text_template_version | Audit/preprocessing; không bắt buộc lưu MySQL |
| embedding_text | Không bắt buộc lưu MySQL; dùng nguyên text cho BGE-M3 |

Importer phải upsert theo `imdb_id`, xác nhận `tmdb_id` không thuộc phim khác,
thực hiện movie và quan hệ trong transaction. Không âm thầm đổi cặp ID khi xung đột.
Deduplicate/upsert các bảng liên kết bằng khóa ghép; chạy lại không tạo trùng.
Các phần tử không có TMDB ID cần xử lý rõ ràng, không tự gán person/genre ID giả.
Không dùng thứ tự dòng JSONL làm movie_id.

Sau import, Khánh Vũ xuất `data/processed/movie_id_mapping.csv`, UTF-8, CSV quoting
đúng cho title có dấu phẩy, với header:

```csv
movie_id,imdb_id,tmdb_id,title
```

Qdrant pipeline join mapping vào full dataset bằng `imdb_id`, kiểm tra lại `tmdb_id`,
movie_id dương và unique. Thiếu mapping hoặc xung đột thì dừng/index-reject có báo cáo;
không dùng TMDB ID thay movie_id. Canonical text giữ template `movie_text_v1`, không
chèn year/rating/votes/runtime vào semantic text. Các trường số dùng payload/filter.

## Kiểm chứng và phần còn lại

- `python3 -m pytest data/tests -q`: 11 tests đạt, gồm 8 tests pipeline mới.
- Kiểm tra bổ sung sau đó: **14 tests đạt**. Validator phát hiện output bị sửa,
  numeric field chèn vào embedding, ID trùng, JSON hỏng, cache sai external ID,
  catalog chưa đủ và phim tham chiếu bị thiếu. HTTP 5xx hết retry chỉ ghi failed
  cho phim đó rồi tiếp tục; lỗi mạng lặp lại/429 kéo dài vẫn dừng batch.
- Dry run 3 phim thật: 3 accepted, 0 rejected, byte-for-byte giống sample committed.
  File `data/processed/dry_run_3/movies_cleaned.jsonl`: 12.202 bytes,
  SHA-256 `a4e9faf06504a9544f2c0901f5da7822341886c35aa656b84dd05d62792293cf`.
- Tests 25 phim dùng fixture giả lập: kiểm tra resume/dedup/cache, không phải dry run
  metadata thật. Tests còn kiểm tra crash trước checkpoint, ID mismatch, duplicate TMDB,
  unmatched/ambiguous find, retry lỗi và Retry-After.
- Còn phải làm: dry run 25 phim thật; chạy validation trên full và kiểm tra 20 phim ngẫu
  nhiên; full run; thống kê thiếu/error/coverage; kích thước và SHA-256 từng full output.

Validator offline đã có, dùng SQLite tạm trên đĩa để phát hiện ID trùng, không giữ
toàn bộ JSONL trong RAM. Mỗi dòng được đối chiếu với checkpoint và raw cache đã
transform lại; báo cáo chứa kích thước/SHA-256, tỷ lệ thiếu, khác biệt so với ba
sample và reservoir 20 phim (seed cố định) để kiểm tra thủ công.

```bash
# Sau khi có output dry run thực tế:
python3 data/scripts/validate_catalog.py \
  --input data/processed/dry_run_25/movies_cleaned_full.jsonl \
  --report data/processed/dry_run_25/validation.json
# Sau full run: bắt buộc kiểm tra coverage và ba phim tham chiếu:
python3 data/scripts/validate_catalog.py --require-complete
```

`passed=true` với `scope=subset` chỉ xác nhận các dòng đã kiểm tra, không xác nhận
full dataset. `manual_review_completed=false` luôn được giữ trong báo cáo máy;
người review cần ghi nhận kết quả thực tế riêng. Chưa chạy validator trên full
vì chưa có metadata cache và full output. Tests validator dùng dữ liệu giả lập.

`data/raw/` và `data/processed/` đã được `.gitignore` loại trừ. Không thấy convention
Git LFS trong repository. Chỉ commit script/test/tài liệu và report nhỏ đã chọn;
không commit dump, cache hoặc credentials. Không upload dataset ra dịch vụ ngoài.
Sau full run sẽ bổ sung vị trí local, size, SHA-256 và hướng dẫn nhận file qua kênh
nhóm do người dùng chỉ định; chưa có artifact full để chia sẻ.
