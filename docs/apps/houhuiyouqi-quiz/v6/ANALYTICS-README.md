# 《后会友期》V6 匿名统计接口

统计代码已安装在正式首页、`/v6/index.html` 和八位人物的 `/v6/share/*.html`。V6 内测页不加载统计脚本。

## 当前状态
**待激活。** 目前无法从已打开的 Umami Cloud 网站列表确认已添加网站，故 `analytics.js` 中 `WEBSITE_ID` 留空。留空时不加载 Umami 远程脚本，不发送访问数据。

在 [Umami Cloud](https://cloud.umami.is/analytics/eu/websites) 点击“添加网站”，名称可用“后会友期 · 友情人物测试”，域名填写 `olivia-wr-research.github.io`（不是完整路径）。保存后，从“追踪代码 / Tracking code”复制形如 `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` 的 **Website ID**。只需将 `analytics.js` 的 `WEBSITE_ID = ''` 更新为该值，再发布即可启用。Website ID 本身是公开标识，不是密码或 API 密钥。

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

匿名 UV 不能等同准确的真人个体数，PV 不能等同答题数。**未启用之前无法追溯历史统计。**

## 查看与验收
正式启用后访问 Umami 网站 Dashboard 查看 PV/Visitors，Events 查看上述事件及转化漏斗。分别验证一次打开首页、一次开始、一次完整答题、一次保存海报、一次分享，以及打开一张独立分享页。由于同一浏览器可能有广告拦截，必要时使用未阻拦统计请求的浏览器核验。
