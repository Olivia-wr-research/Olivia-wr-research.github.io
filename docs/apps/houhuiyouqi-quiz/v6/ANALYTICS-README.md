# 《后会友期》V6 匿名统计接口

统计代码已安装在正式首页、`/v6/index.html` 和八位人物的 `/v6/share/*.html`。V6 内测页不加载统计脚本。

## 当前状态
**已启用。** Website ID 已从账号内 Umami Settings 页核验并写入 `analytics.js`：`eb5fafdb-5785-44d4-a4c0-00cfc6072304`。网站域名核对为 `olivia-wr-research.github.io`。只有在 GitHub Pages 生产域名的公开网页打开、浏览器未阻止远程跟踪请求时才会尝试向 Umami 发送统计数据。启用不代表已经确认 Umami 收到了事件。

现有 Umami Cloud 网站已经创建，后台地址：https://cloud.umami.is/analytics/eu/websites/eb5fafdb-5785-44d4-a4c0-00cfc6072304 。Website ID 是公开标识，不是密码或 API 密钥；后续换站点时需同步更新此 ID。

## 定义
- 自动 PV（访问次数）及访客数：Umami 跟踪脚本加载后自动记录页面浏览，访客数是匿名估算。
- `quiz_start`：进入新一轮答题（包括重测），不包括单纯浏览首页。
- `quiz_complete`：完成第十题，成功计算结果，每轮最多一次。
- `poster_view_requested`：点击跳转海报选择区。
- `poster_generated`：成功将海报绘制并导出为图片数据，不等于已保存到手机相册。
- `share_clicked`：点击分享按钮，不等于已成功分享到社交平台。
- `share_copy_requested`：用户请求复制文案或分享链接（不承诺操作系统剪贴板成功）。
- `share_native_completed`：设备原生分享接口成功返回，不能验证收件人是否收到。
- 独立分享页的访问：`/v6/share/{人物}.html` 自动 PV，无需额外事件。

## 隐私与限制
不向统计 API 发送逐题答案、用户上传照片、姓名、联系方式或自定义访客 ID。设置 `data-exclude-search` 与 `data-exclude-hash`，避免提交 URL 查询参数。限定 GitHub Pages 站点域名，不对测试页或其他站点自动采集数据。浏览器拦截、网络故障或 DNT 会降低可计数人数。Umami Cloud 是第三方处理方，实际网络请求会涉及浏览器技术信息；运营者需核查适用隐私规则。

匿名 UV 不能等同准确的真人个体数，PV 不能等同答题数。**本次启用之前产生的历史访问无法追溯。** 实际产生数据的起始时间以 Umami 接收第一条事件为准。

## 查看与验收
正式启用后访问 Umami 网站 Dashboard 查看 PV/Visitors，Events 查看上述事件及转化漏斗。分别验证一次打开首页、一次开始、一次完整答题、一次保存海报、一次分享，以及打开一张独立分享页。由于同一浏览器可能有广告拦截，必要时使用未阻拦统计请求的浏览器核验。
