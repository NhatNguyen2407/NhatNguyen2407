# Kết nối góc âm nhạc

Profile có thể upload trước. Khi chưa có snapshot, phần âm nhạc hiện một card chờ kết nối và link hướng dẫn; không có bài hát hay bảng xếp hạng giả.

Workflow phải ở đúng `.github/workflows/music.yml`, không phải `workflows/music.yml`. Lần upload ban đầu bị thiếu cấp `.github`; đường dẫn này đã được sửa trong repo. Chạy thành công workflow profile chưa đồng nghĩa Spotify đã được ủy quyền.

## Spotify hiện tại

Bro cần Python 3 trên máy để thực hiện bước kết nối một lần. Phần này không cần deploy Vercel hay tạo backend riêng.

1. Mở [Spotify Developer Dashboard](https://developer.spotify.com/dashboard), tạo app cá nhân dùng Web API. Tài khoản sở hữu app hiện cần Spotify Premium.
2. Trong app settings, thêm đúng redirect URI: `http://127.0.0.1:8765/callback`. Dùng địa chỉ này, không thay bằng `localhost`.
3. Lấy Client ID của app. Nếu app yêu cầu allowlist, thêm tài khoản Spotify của Bro ở phần Users and Access.
4. Mở PowerShell tại thư mục source đã giải nén và chạy:

```powershell
py -3 tools/connect_spotify.py
```

5. Nhập Client ID khi script hỏi. Trình duyệt của Bro sẽ mở Spotify để cấp hai quyền đọc: bài đang phát và top artists. Script không điều khiển phát nhạc.
6. Sau khi xong, script lưu `.spotify-secrets.json` trên máy. Mở file đó tại máy Bro để lấy hai giá trị. File này đã nằm trong `.gitignore`; không upload và không gửi nội dung vào chat.
7. Trong repo profile, vào **Settings > Secrets and variables > Actions**:

| Tab | Name | Value |
| --- | --- | --- |
| Variables | `MUSIC_PROVIDER` | `spotify` |
| Variables | `SPOTIFY_CLIENT_ID` | Client ID từ file local |
| Secrets | `SPOTIFY_REFRESH_TOKEN` | Refresh token từ file local |

8. Mở **Actions > Refresh music snapshot > Run workflow**. Khi workflow thành công, ảnh bài đang phát ở lần kiểm tra gần nhất và top 5 sẽ tự xuất hiện trong README.

Top 5 là affinity ranking của Spotify trong khoảng bốn tuần gần nhất, không phải số lượt nghe. Ảnh cập nhật theo lịch khoảng 30 phút và có thời điểm kiểm tra; GitHub có thể cache ảnh nên nó không phản ánh nhạc theo từng giây.

Theo tài liệu Spotify được kiểm tra ngày 30/10/2026, refresh token của app đăng ký trong Developer Dashboard có thời hạn sáu tháng. Khi token hết hạn hoặc bị thu hồi, chạy lại bước kết nối và thay secret. Nếu Bro ngừng Premium, app Development Mode có thể ngừng hoạt động.

## Chuyển sang YouTube Music sau này

Đã có sẵn adapter Last.fm trong source để không phải viết lại giao diện.

1. Tạo tài khoản Last.fm và kết nối một trình scrobble phù hợp với thiết bị nghe của Bro, chẳng hạn [Web Scrobbler](https://web-scrobbler.com/) khi dùng YouTube Music trong trình duyệt.
2. Kiểm tra bài hát thật đã được ghi nhận trên Last.fm. Việc nghe trên điện thoại hoặc offline cần một đường ghi nhận riêng; không mặc định mọi thiết bị đều được bao phủ.
3. Tạo [Last.fm API key](https://www.last.fm/api/account/create), rồi đặt `LASTFM_USERNAME` ở Variables và `LASTFM_API_KEY` ở Secrets.
4. Đổi Variable `MUSIC_PROVIDER` thành `lastfm` và chạy lại **Refresh music snapshot**.

Nguồn Last.fm chỉ xếp hạng các lượt nghe đã ghi nhận. Nó không tự nhập toàn bộ lịch sử Spotify hay YouTube Music cũ.

## Tài liệu nguồn

- [Spotify PKCE](https://developer.spotify.com/documentation/web-api/tutorials/code-pkce-flow)
- [Redirect URIs](https://developer.spotify.com/documentation/web-api/concepts/redirect_uri)
- [Refreshing tokens](https://developer.spotify.com/documentation/web-api/tutorials/refreshing-tokens)
- [Quota modes](https://developer.spotify.com/documentation/web-api/concepts/quota-modes)
