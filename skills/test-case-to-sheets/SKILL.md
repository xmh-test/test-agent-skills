---
name: test-case-to-sheets
description: >
  将 test-case-generator 生成的 JSON 测试用例明细转换为本地 Excel（.xlsx）文件。
  适用于用户提到“测试用例转 Excel”、“JSON 转 Excel”、“测试用例导出”、“测试用例转换”、“生成测试用例表格”、
  “将测试用例 JSON 转表格”等场景。默认读取测试用例 JSON，校验标准字段，并使用技能内置 Python 脚本
  生成同目录同名的 .xlsx 文件。
---

# 测试用例 JSON 转 Excel

将 `test-case-generator` 生成的测试用例 JSON 明细文件转换为本地 Excel 文件。生成的 `.xlsx` 必须保存到 JSON 文件相同目录，默认文件名为 `{JSON文件名}.xlsx`。

## 输入定位

1. 优先使用用户明确提供的 JSON 文件路径。
2. 未指定时，在当前工作区或 `test_cases/` 目录下查找最新的 `测试用例_*.json`。
3. 只读取 JSON 明细文件；MD 总结文件不是转换数据源。
4. 如果用户给的是目录，查找该目录下最新的 `测试用例_*.json`。

## 标准字段

JSON 顶层应为数组，每条用例通常包含以下 9 个字段：

| JSON 字段             | Excel 列名 | 处理规则                   |
| ------------------- | -------- | ---------------------- |
| `title`             | 用例名称     | 直接写入                   |
| `directory`         | 所属目录     | 直接写入                   |
| `tags`              | 标签       | 数组转为 `、` 分隔字符串         |
| `priority`          | 优先级      | 直接写入，支持 P0/P1/P2 着色 |
| `case_type`         | 用例类型     | 直接写入                   |
| `precondition`      | 前置条件     | 保留换行和编号                |
| `steps`             | 步骤       | 保留换行和编号                |
| `expected`          | 预期结果     | 保留换行和编号                |
| `functional_module` | 功能模块     | 直接写入                   |

脚本会额外生成 `序号` 列。

## 转换流程

1. 确认输入 JSON 文件存在。
2. 使用本技能同目录下的 `scripts/json_test_cases_to_excel.py` 转换：

```bash
python3 scripts/json_test_cases_to_excel.py <测试用例JSON路径>
```

3. 如需指定输出文件，仍必须放在 JSON 同目录：

```bash
python3 scripts/json_test_cases_to_excel.py <测试用例JSON路径> -o <同目录输出文件.xlsx>
```

4. 转换完成后，向用户返回生成的 Excel 文件绝对路径和转换条数。

## 输出要求

- 默认输出路径：输入 JSON 同目录、同文件名、扩展名改为 `.xlsx`。
- Excel 表头固定为：`序号`、`用例名称`、`所属目录`、`标签`、`优先级`、`用例类型`、`前置条件`、`步骤`、`预期结果`、`功能模块`。
- Excel 应保留单元格换行，冻结首行，启用筛选，设置适合阅读的列宽。

## 校验与失败处理

- 如果 JSON 不存在、无法解析、根节点不是数组或对象中不含用例数组，停止并说明原因。
- 如果某条用例不是对象，停止并指出序号。
- 如果转换命令失败，返回错误输出，不生成替代格式。
- 转换后建议检查 `.xlsx` 文件存在，并用 zip/XML 方式做基本完整性校验：

```bash
python3 -c "import zipfile,sys; z=zipfile.ZipFile(sys.argv[1]); print(z.testzip())" <输出xlsx路径>
```

## 注意事项

- 不要从 MD 总结中还原 `steps` 或 `expected` 明细。
