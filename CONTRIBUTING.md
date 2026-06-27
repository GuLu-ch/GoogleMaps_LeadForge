# 贡献指南

感谢关注 GoogleMaps_LeadForge。本项目当前处于早期开发阶段，欢迎通过 Issue、文档改进、测试用例和代码贡献参与。

## 基本要求

- 所有文档和代码注释默认使用中文。
- 提交前必须运行相关测试。
- 修改功能、目录、配置、数据库结构或运行方式时，必须同步更新文档。
- 不实现自动绕过验证码、登录限制、访问限制或风控机制的功能。

## 开发流程

1. 确认需求。
2. 确认技术路线。
3. 更新相关文档。
4. 编写测试。
5. 实现代码。
6. 运行验证。
7. 提交变更。

详细规则见 `AGENTS.md` 和 `docs/DEVELOPMENT_WORKFLOW.md`。

## 本地验证

```powershell
& 'D:\WorkSpace\Python\GMap\.conda\gmap\python.exe' -m pytest tests/unit -v
& 'D:\WorkSpace\Python\GMap\.conda\gmap\python.exe' -m gmap_collector.main --check
```

## 提交信息建议

- `docs: update project documentation`
- `feat: add keyword task builder`
- `fix: correct export encoding`
- `test: add sqlite repository tests`
