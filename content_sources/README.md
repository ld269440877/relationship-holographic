# Content Sources / 原始内容资产

此目录用于逐步把项目根目录中的历史 JSON、Markdown、HTML、legacy JS 内容资产与代码目录分离。

目标原则：

```text
content_sources/* 只保存原始导入源
data/* 只保存 SQLite 与运行期数据
backend/* 只保存后端代码
frontend/* 只保存前端代码
docs/* 只保存审计与工程文档
```

当前导入脚本已支持优先读取：

- `content_sources/raw_json/`
- `content_sources/raw_markdown/`
- `content_sources/raw_html/`
- `content_sources/legacy_js/`

如果目标文件暂未迁移到本目录，脚本会自动回退读取项目根目录的历史文件，保证兼容。
