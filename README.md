# 我的成长主页

一个用原生 HTML/CSS/JavaScript 写的个人学习记录与技能展示站。页面由 Jinja2 模板生成，真实姓名、邮箱、学校等信息通过环境变量注入，公开仓库中只保留占位符。

## 项目说明

站点包含三个可互相跳转的独立页面：

- `index.html`：首页，包含关于我、作品说明（100–200 字）、首页结构预览、联系方式与留言表单；
- `learn.html`：学习记录，至少三条，每条按“时间 / 学了什么 / 遇到什么问题 / 怎么解决”四栏书写，并支持关键词筛选；
- `projects.html`：技能展示与项目作品，附页面内代码片段证据和仓库链接。

全站使用响应式布局，支持浅色/深色主题切换，无后端、无第三方依赖。

## 目录结构

```
.
├── build.py                  # Jinja2 构建脚本
├── requirements.txt          # Python 依赖
├── .env.example              # 环境变量示例（复制为 .env）
├── templates/                # 模板与静态资源
│   ├── base.html
│   ├── index.html
│   ├── learn.html
│   ├── projects.html
│   ├── submission_manifest.html
│   ├── style.css
│   └── script.js
├── .github/workflows/        # 可选的 GitHub Pages 构建部署
├── dist/                     # 构建产物（含真实信息，已被忽略）
└── README.md
```

## 环境要求

- Python 3.10 或更高版本
- Jinja2（见 `requirements.txt`）

## 快速开始

```bash
python -m pip install -r requirements.txt
```

复制环境变量示例并填写自己的信息：

```bash
cp .env.example .env
```

Windows PowerShell：

```powershell
Copy-Item .env.example .env
```

`.env` 至少需要填写：`AUTHOR_NAME`、`CONTACT_EMAIL`、`GITHUB_USER`、`GITHUB_REPO`、`SITE_TITLE`、`SITE_SUBTITLE`、`SCHOOL`、`MAJOR`、`GRADE`。`PAGES_URL` 可选，未部署时留空。

构建：

```bash
python build.py
```

构建成功后输出到 `dist/`：

- `dist/index.html`、`dist/learn.html`、`dist/projects.html`
- `dist/style.css`、`dist/script.js`
- `dist/README.md`
- `dist/submission/index.html`：课程平台单文件提交包

## 运行方式

直接打开 `dist/index.html` 即可；或在 `dist/` 下启动一个静态服务器：

```bash
cd dist
python -m http.server 8000
```

然后访问 `http://localhost:8000/`。

## 部署到 GitHub Pages

`dist/` 包含真实联系方式，**不要提交到公开仓库**。推荐用 GitHub Actions 在仓库 Secrets 中注入环境变量，构建后直接部署 Pages：

1. 在仓库 Settings → Secrets and variables → Actions 中添加 `AUTHOR_NAME`、`CONTACT_EMAIL`、`SCHOOL`、`MAJOR`、`GRADE`、`SITE_TITLE`、`SITE_SUBTITLE`；
2. 在 Settings → Pages 中将 Source 设为 GitHub Actions；
3. 手动运行 `.github/workflows/pages.yml`；
4. 部署完成后，把 Pages 地址填入本地 `.env` 的 `PAGES_URL`，重新运行 `python build.py`，再生成最终提交包。

如果暂时不部署，可以跳过本节；评分标准中 GitHub Pages 是鼓励项，不是强制项。

## 隐私

- 公开模板、README 和构建脚本只使用占位符；真实信息只存在于被忽略的 `.env` 和 `dist/` 中；
- `build.py` 在构建前会检查公开文件是否意外包含真实姓名、邮箱或学校，发现后直接失败；
- 提交前请确认 `git status` 中没有 `.env`、`dist/` 或其它包含隐私的文件；
- 课程平台提交包 `dist/submission/index.html` 会包含联系方式，请只提交到课程平台，不要上传到公开仓库。

## 更新规范

- 每条学习记录固定四栏：时间 / 学了什么 / 遇到什么问题 / 怎么解决或还没解决什么；
- 时间格式统一为 `YYYY/MM`，新记录放在最上面；
- 技能与项目尽量附代码片段、截图或可访问链接，不写“熟悉/了解”；
- 每次更新后同步修改 `.env` 中的 `LAST_UPDATED`，并重新构建；
- 提交信息遵循 `提交类型(影响域): 中文一句话简要说明`。

## 许可证

MIT，见 `LICENSE`。
