---
name: test-case-to-sheets
description: >
  将 test-case-generator 或 test-api-generator 生成的 JSON 测试用例明细转换为飞书电子表格。
  适用于需要将测试用例 JSON 导入飞书表格进行协作管理的场景。
  当用户提到 "将测试用例转飞书表格"、"JSON转表格"、"导出测试用例到飞书"、"测试用例导出"、"测试用例转换" 时使用此 skill。
  会校验并映射用例名称、所属目录、标签、优先级、用例类型、前置条件、步骤、预期结果、功能模块等标准字段。
---

# JSON 测试用例转飞书表格

将 `test-case-generator` 或 `test-api-generator` 输出的 JSON 明细文件转换为飞书电子表格。MD 总结文件只用于辅助核对统计，不作为数据源。

## 转换流程

### 1. 定位输入文件

- 优先使用用户明确提供的 JSON 文件路径
- 未指定时，在当前工作区或 `test_cases/` 目录下查找最新的 `测试用例_*.json` 或 `接口测试用例_*.json`
- 如用户同时提供 MD 总结文件，只读取其统计信息用于一致性核对，不从 MD 中解析具体用例

### 2. 解析 JSON 明细

JSON 必须是数组结构，每条用例必须有且仅有以下 9 个标准字段：

| JSON 字段 | 飞书表格字段 | 处理规则 |
|----------|--------------|----------|
| `title` | 用例名称 | 直接使用 |
| `directory` | 所属目录 | 直接使用，格式应为 `项目名|平台分类|模块名` |
| `tags` | 标签 | 数组转为逗号分隔字符串 |
| `priority` | 优先级 | 仅允许 `P0` / `P1` / `P2` / `P3` |
| `case_type` | 用例类型 | 直接使用，复合类型保留 `|` |
| `precondition` | 前置条件 | 保留 `\n` 换行和编号 |
| `steps` | 步骤 | 保留 `\n` 换行和编号 |
| `expected` | 预期结果 | 保留 `\n` 换行和编号 |
| `functional_module` | 功能模块 | 直接使用 |

### 3. 数据校验

写入飞书前必须完成以下校验：

- JSON 可解析且顶层为数组
- 每条用例有且仅有 9 个标准字段
- `directory` 不为空，且为三段格式：`项目名|平台分类|模块名`
- `functional_module` 与 `directory` 第三段模块名一致
- `tags` 为字符串数组
- `steps` 与 `expected` 的编号条数一致
- 不保留 `{字段名}`、`${TIMESTAMP}` 等未替换占位符

校验失败时，先向用户说明具体错误位置，不写入飞书表格。

### 4. 输出到飞书表格

使用 `lark-sheets` 技能将数据写入飞书电子表格。

#### 4.1 创建新表格

使用 `lark-cli sheets +create` 创建新电子表格：

```bash
lark-cli sheets +create \
  --title "{原文件名}_测试用例" \
  --values '[["用例名称","所属目录","标签","优先级","用例类型","前置条件","步骤","预期结果","功能模块"], {数据行...}]'
```

- 第一行为固定表头
- 后续每行对应一条测试用例
- 如果用户指定已有飞书表格 URL/token，则使用 `+write` 或 `+append`

#### 4.2 写入已有表格

```bash
lark-cli sheets +append --url "<表格URL>" --values '[[数据行1], [数据行2], ...]'
```

或：

```bash
lark-cli sheets +write --url "<表格URL>" --sheet-id "<sheet_id>" --range "A2" --values '[[数据行1], ...]'
```

#### 4.3 设置表头样式（可选）

```bash
lark-cli sheets +set-style --url "<表格URL>" --range "A1:I1" --style '{"fontWeight":"bold","backgroundColor":"#f0f0f0"}'
```

#### 4.4 输出结果

操作完成后，向用户返回飞书表格 URL，并说明写入的用例数量。

## 注意事项

- 必须使用飞书相关 skill 操作表格；禁止自行绕过飞书工具直接调用 API
- 单元格换行符直接使用 `\n`
- 如果表格数据量超过 1000 行，建议分批写入，每次不超过 500 行
- 不要从 MD 总结中还原步骤或预期，MD 不是用例明细数据源
