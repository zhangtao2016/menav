# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库中工作时提供指导。

## 项目概览

MeNav — 静态个人导航网站生成器。YAML 配置 + Handlebars 模板 → 静态 HTML。无数据库，无后端。产物输出到 `dist/`。

## 命令

```bash
npm run dev              # 开发服务器，热重载（会刷新在线缓存）
npm run dev:offline      # 开发服务器，不刷新缓存
npm run build            # 完整构建：clean → sync-*（best-effort）→ generate → bundle runtime
npm test                 # 运行全部测试（Node.js 原生测试运行器）
npm run lint             # 语法检查所有 JS 文件（node --check）
npm run format           # Prettier --write
npm run format:check     # Prettier --check
npm run check            # 顺序执行：lint → test → build
npm run import-bookmarks # 将浏览器书签 HTML 转换为 config/user/pages/bookmarks.yml
npm run sync-articles    # 抓取 RSS 源，缓存写入 dev/（best-effort）
npm run sync-projects    # 抓取 GitHub 仓库元信息，缓存写入 dev/（best-effort）
```

运行单个测试：`node --test test/<file>.node-test.js`

## 架构

两阶段架构：**构建期**（generator）生成静态 HTML，**浏览器运行时**（SPA）提供交互。

### 生成端（构建期）— `src/generator/`

入口：`src/generator.js`（薄入口，委托到 `main.js`）。

流水线：config load → validate → resolve → prepare page data → render Handlebars → write `dist/`。

- **config/** — `loader.js` 从文件系统加载 YAML；`validator.js` 校验并填充默认值；`resolver.js` 准备渲染数据；`slugs.js` 生成唯一分类标识符
- **html/** — `page-data.js` 组装每页模板数据；`components.js` 生成导航/分类/社交链接；`fonts.js` 处理字体 CSS/链接；`404.js` 生成 404 页面
- **cache/** — `articles.js`（RSS）、`projects.js`（GitHub 元数据）。缓存位于 `dev/`（已 gitignore）
- **template/engine.js** — 加载 `.hbs` 文件，自动将 `templates/components/*.hbs` 注册为 partial

### 运行时（浏览器）— `src/runtime/`

入口：`src/runtime/index.js`。由 esbuild（`scripts/build-runtime.js`）打包为 `dist/script.js`（IIFE，压缩，ES2018 目标）。

- **app/routing.js** — SPA 页面切换，基于 URL hash 的路由
- **app/search.js** — 客户端搜索索引，搜索引擎切换
- **app/ui.js** — 侧边栏切换、主题切换、滚动行为
- **app/searchEngines.js** — 外部搜索引擎配置
- **app/search/highlight.js** — 搜索结果高亮
- **menav/** — `window.MeNav` 扩展 API（增/改/删元素，事件系统）。供 MarksVault 浏览器扩展使用
- **nested/index.js** — 多层级书签展开/折叠（2-4 层）
- **tooltip.js** — 站点卡片悬停提示
- **shared.js** — URL 校验、class 清洗、视口高度

### 辅助函数 — `src/helpers/`

生成器初始化时注册的 Handlebars 模板助手：`formatters.js`、`conditions.js`、`utils.js`。

### 配置系统 — `config/`

完全替换策略（非合并）：若 `config/user/` 存在，则完全替换 `config/_default/`。若 `config/user/site.yml` 缺失，构建直接报错退出。

结构：

- `config/_default/site.yml` — 站点元信息、导航、个人资料、字体、主题、图标、RSS、GitHub 设置
- `config/_default/pages/*.yml` — 各页面内容（categories → sites）
- `config/user/` — 用户覆盖（镜像 `_default/` 结构，切勿在此提交默认配置）

`site.yml → navigation[].id` 中的页面 ID 对应 `pages/<id>.yml`。导航第一项 = 首页。

### 模板 — `templates/`

- `layouts/default.hbs` — 完整 HTML 骨架（doctype、head、body）
- `pages/*.hbs` — 页面内容片段（插入布局的 `{{{body}}}` 中）
- `components/*.hbs` — 自动注册的 partial（category、group、site-card、navigation、page-header 等）

每页模板解析顺序：显式 `template` 字段 → page-id 匹配 → 回退到 `page.hbs`。

## 关键模式

- **YAML 贯穿全局**：所有配置均为 YAML。使用 `js-yaml` 读写。
- **完全替换**：user 与 default 配置从不合并，只选一套。
- **Best-effort 同步**：`sync-articles`/`sync-projects` 失败绝不阻断构建。
- **构建期内容页**：`template: content` 页面在构建时将 Markdown 渲染为 HTML（非运行时抓取）。禁止 raw HTML，禁止图片，链接按 `security.allowedSchemes` 白名单校验。
- **配置权威来源**：site/page 的 YAML 结构以 `config/_default/` 中的默认文件为准，而非文档注释。
- **运行时扩展契约**：`window.MeNav` API 是 MeNav 与 MarksVault 之间的契约。未经对应扩展更新，不得破坏此 API。

## 测试

测试使用 Node.js 内置 `node:test`（无 Jest/Mocha）。测试文件位于 `test/`，后缀为 `.node-test.js`。测试通过临时配置目录启动 `src/generator.js` 并对生成的 `dist/` 产物做断言——测试的是完整构建流水线，而非单元级别的 mock。
