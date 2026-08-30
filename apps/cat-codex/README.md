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
- `src-tauri/src/transport.rs` is the native transport seam. It currently
  reports `NotConfigured`; stdio/Unix/WebSocket implementations can be added
  behind the same seam without platform-specific UI changes.
- This repository has validated the TypeScript build plus macOS `.app`/`.dmg`
  bundling. A Windows package still requires a Windows CI/runner with the
  WebView2 and Tauri prerequisites; it is not claimed as a produced Windows
  artifact yet.

生产构建：

```bash
npm run build
```

## Integration boundaries

- `src/lib/codex/transport.ts`：可替换 transport。当前提供浏览器 WebSocket transport，以及明确抛出“native transport unavailable”的 placeholder；未来 Tauri shell 可以注入 stdio / Unix socket 实现。
- `src/lib/codex/client.ts`：Codex App Server client，按官方生命周期发送 `initialize`、`initialized`、`thread/start`、`turn/start`，响应与通知分开处理。
- `src/lib/codex/types.ts`：官方协议请求、响应、初始化、thread/start、turn/start 与通知的 TypeScript 边界。没有把 UI demo 数据伪装成服务器结果。
- `src/lib/providers.ts`：Provider 类型和模型边界，预留 OpenAI/Codex、DeepSeek、Claude、Gemini、本地模型与 OpenAI-compatible。
- `src/lib/plugins.ts`：插件 manifest 与 extension point 边界。插件可扩展 Provider、工具、MCP、技能、面板或工作流；第一阶段注册表为空。

当前 UI 默认显示 `Not connected`。没有 app-server endpoint 或 native shell 时，发送请求只显示“未发送”提示，不产生虚假成功事件。

官方协议依据：[Codex App Server 文档](https://developers.openai.com/codex/app-server)。
