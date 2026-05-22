# AI Agent Test Skills

一套面向 AI Agent 的**测试全生命周期**技能集合，覆盖从需求分析到测试用例生成、评审、导出的完整工作流。

## 特性

- **自动化驱动**：通过自然语言交互即可生成标准化测试文档
- **高质量输出**：内置质量保障流程（生成 → 自检 → 修复 → 输出）
- **多平台支持**：覆盖 Web、iOS/Android、桌面端测试场景
- **可集成**：输出格式可直接对接飞书等协作平台

## 技能列表

### 需求阶段

| Skill | 触发词 | 说明 |
|-------|--------|------|
| `requirements-analyst` | "分析需求"、"需求文档" | 深度分析产品需求，输出结构化 Markdown 需求分析文档，包含显式/隐式需求识别、业务流程梳理、数据模型分析、影响面分析和需求缺口识别 |
| `requirements-confirm` | "口头需求"、"确认需求"、"需求记录" | 将口头需求或简短描述转换为结构化的需求确认文档，适用于测试团队收到非正式需求后留下文字记录 |
| `test-plan` | "测试计划"、"制定测试方案" | 根据已确认需求生成结构化测试计划文档，明确测试范围、策略、排期和上线标准 |

### 测试用例阶段

| Skill | 触发词 | 说明 |
|-------|--------|------|
| `test-case-generator` | "生成测试用例"、"写用例"、"test case" | 基于需求文档生成高规范标准格式的功能测试用例，包含循环迭代质量保障流程，确保用例达到理想质量阈值 |
| `test-case-reviewer` | "评审用例"、"用例审查" | 评审已有测试用例质量，检查覆盖度、可执行性、可验证性、独立性等维度，输出结构化评审报告 |
| `test-e2e-scenarios` | "E2E测试"、"端到端场景" | 基于需求输出端到端场景化测试用例，以用户旅程为主线描述跨模块/跨页面的完整操作流程 |
| `test-api-generator` | "接口测试"、"API用例"、"RESTful测试" | 基于 API 文档/接口描述生成高覆盖、可执行的 API 接口测试用例，覆盖功能正确性、参数校验、鉴权、安全基线等维度 |

### 协作导出

| Skill | 触发词 | 说明 |
|-------|--------|------|
| `test-case-to-sheets` | "转飞书表格"、"MD转表格"、"导出测试用例" | 将 Markdown 测试用例文档转换为飞书电子表格，自动补全所属目录、标签、用例类型等字段 |

## 推荐工作流

```
需求输入 → requirements-confirm / requirements-analyst
              ↓
         test-plan (可选)
              ↓
    test-case-generator → test-case-reviewer (迭代)
              ↓
    test-e2e-scenarios / test-api-generator (按需)
              ↓
       test-case-to-sheets (导出协作)
```

## 安装

将 `skills/` 目录复制到你的项目或 Claude Code 配置目录中：

```bash
# 方式 1：复制到项目根目录
cp -r skills/ your-project/

# 方式 2：复制到 Claude Code 全局 skills 目录
cp -r skills/ ~/.claude/skills/
```

## 目录结构

```
skills/
├── requirements-analyst/       # 需求分析
│   ├── SKILL.md
│   └── references/
│       └── requirements_template.md
├── requirements-confirm/       # 需求确认
│   └── SKILL.md
├── test-plan/                  # 测试计划
│   └── SKILL.md
├── test-case-generator/        # 功能测试用例生成
│   ├── SKILL.md
│   └── references/
│       └── test_case_template.md
├── test-case-reviewer/         # 用例质量评审
│   ├── SKILL.md
│   └── references/
│       └── review_checklist.md
├── test-e2e-scenarios/         # E2E 场景用例
│   ├── SKILL.md
│   └── references/
│       └── e2e_scenario_template.md
├── test-api-generator/         # API 接口测试
│   ├── SKILL.md
│   └── references/
│       └── api_test_template.md
└── test-case-to-sheets/        # 导出到飞书
    └── SKILL.md
```

## 使用示例

### 生成测试用例

```
/test-case-generator 用户登录功能的需求文档如下：
- 支持手机号+验证码登录
- 支持密码登录
- 连续失败5次锁定30分钟
```

### 评审已有用例

```
/test-case-reviewer 请评审以下测试用例：
[粘贴用例内容或指定文件路径]
```

### 导出到飞书

```
/test-case-to-sheets 将 test_cases.md 转换为飞书表格
```

## License

MIT
