# Cat Codex workbench

第一阶段的可启动跨平台桌面工作台。React/TypeScript UI 由 Tauri 2 壳承载，交互结构参考用户熟悉的 Codex 桌面工作台：左侧项目/会话，中间对话与 Agent events，右侧 Files / Diff / Output / Plugins 检查器，底部输入和模型/权限状态。

## Run

```bash
npm install
npm run dev
```

桌面壳开发与构建（需要 Rust、系统 WebView 与 Tauri 2 CLI）：

```bash
npm run tauri:dev
npm run tauri:build
```

## Platform boundary

- Tauri 2 targets macOS and Windows from the same `src-tauri` project. Window
  sizing, path separators, platform identity, and native command registration
  stay inside the shell; the React information architecture is shared.
- `src/lib/platform.ts` keeps platform, App Server endpoint, sandbox/permission
  mode, and network policy abstract. The native shell owns secret-bearing
  headers and local process launch; the browser UI never stores raw API keys.
- `src-tauri/src/transport.rs` owns the native stdio transport. Tauri starts
  the official `codex app-server --stdio` process, writes JSONL requests to its
  stdin, and emits stdout messages to the React client as Tauri events.
- This repository has validated the TypeScript build plus macOS `.app`/`.dmg`
  bundling. A Windows package still requires a Windows CI/runner with the
  WebView2 and Tauri prerequisites; it is not claimed as a produced Windows
  artifact yet.

生产构建：

```bash
npm run build
```

## Integration boundaries

- `src/lib/codex/transport.ts`：可替换 transport。Tauri 桌面壳使用原生 stdio transport；浏览器预览继续使用明确失败的 placeholder，避免把网页环境误当成原生连接。
- `src/lib/codex/client.ts`：Codex App Server client，按官方生命周期发送 `initialize`、`initialized`、`thread/start`、`turn/start`，响应与通知分开处理。
- `src/lib/codex/types.ts`：官方协议请求、响应、初始化、thread/start、turn/start 与通知的 TypeScript 边界。没有把 UI demo 数据伪装成服务器结果。
- `src/lib/providers.ts`：Provider 类型和模型边界，预留 OpenAI/Codex、DeepSeek、Claude、Gemini、本地模型与 OpenAI-compatible。
- `src/lib/plugins.ts`：插件 manifest 与 extension point 边界。插件可扩展 Provider、工具、MCP、技能、面板或工作流；第一阶段注册表为空。

浏览器预览没有 native shell 时仍显示 `Not connected`；Tauri 桌面壳会启动本机 `codex app-server --stdio`，按官方生命周期完成握手、thread/start 和 turn/start，并通过事件流接收服务端消息。

官方协议依据：[Codex App Server 文档](https://developers.openai.com/codex/app-server)。
