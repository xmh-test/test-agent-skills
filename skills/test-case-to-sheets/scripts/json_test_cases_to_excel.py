#!/usr/bin/env python3
"""
Convert test-case JSON files to Excel .xlsx files.

Usage:
  python3 scripts/json_test_cases_to_excel.py test_cases/MINISPHOTO/相册备份/测试用例_20260525_145457.json
  python3 scripts/json_test_cases_to_excel.py input.json -o output.xlsx

The script uses only Python standard-library modules and writes a real .xlsx
workbook directly, so no pandas/openpyxl dependency is required.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any


COLUMNS = [
    ("序号", "__index__"),
    ("用例名称", "title"),
    ("所属目录", "directory"),
    ("标签", "tags"),
    ("优先级", "priority"),
    ("用例类型", "case_type"),
    ("前置条件", "precondition"),
    ("步骤", "steps"),
    ("预期结果", "expected"),
    ("功能模块", "functional_module"),
]

COLUMN_WIDTHS = [8, 44, 24, 22, 10, 18, 42, 48, 54, 18]
PRIORITY_STYLES = {"P0": 2, "P1": 3, "P2": 4}
INVALID_XML_RE = re.compile(
    r"[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD]",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="将测试用例 JSON 转换为 Excel .xlsx 文件。",
    )
    parser.add_argument("json_file", help="测试用例 JSON 文件路径")
    parser.add_argument(
        "-o",
        "--output",
        help="输出 .xlsx 文件路径；默认与 JSON 同目录同名",
    )
    parser.add_argument(
        "--sheet-name",
        default="测试用例",
        help="工作表名称，默认：测试用例",
    )
    return parser.parse_args()


def load_cases(json_path: Path) -> list[dict[str, Any]]:
    with json_path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if isinstance(payload, list):
        cases = payload
    elif isinstance(payload, dict):
        cases = None
        for key in ("cases", "test_cases", "items", "data", "rows"):
            value = payload.get(key)
            if isinstance(value, list):
                cases = value
                break
        if cases is None:
            raise ValueError(
                "JSON 根对象不是数组，也未找到 cases/test_cases/items/data/rows 数组字段",
            )
    else:
        raise ValueError("JSON 根节点必须是数组或对象")

    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(cases, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"第 {index} 条用例不是 JSON 对象")
        normalized.append(item)
    return normalized


def column_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def cell_ref(row: int, column: int) -> str:
    return f"{column_name(column)}{row}"


def clean_text(value: Any) -> str:
    if value is None:
        text = ""
    elif isinstance(value, list):
        text = "、".join(str(item) for item in value)
    elif isinstance(value, dict):
        text = json.dumps(value, ensure_ascii=False)
    else:
        text = str(value)
    return INVALID_XML_RE.sub("", text)


def xml_text(value: Any) -> str:
    return escape(clean_text(value), quote=False)


def safe_sheet_name(name: str) -> str:
    cleaned = re.sub(r"[\[\]\:\*\?\/\\]", "_", name).strip() or "Sheet1"
    return cleaned[:31]


def row_height(values: list[Any], is_header: bool = False) -> int:
    if is_header:
        return 28
    max_lines = 1
    for value in values:
        max_lines = max(max_lines, clean_text(value).count("\n") + 1)
    return min(max(22, max_lines * 16), 140)


def cell_xml(row: int, column: int, value: Any, style: int = 0) -> str:
    ref = cell_ref(row, column)
    return (
        f'<c r="{ref}" s="{style}" t="inlineStr">'
        f'<is><t xml:space="preserve">{xml_text(value)}</t></is>'
        "</c>"
    )


def worksheet_xml(cases: list[dict[str, Any]]) -> str:
    row_count = len(cases) + 1
    col_count = len(COLUMNS)
    last_ref = cell_ref(max(row_count, 1), col_count)

    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">',
        f'<dimension ref="A1:{last_ref}"/>',
        "<sheetViews><sheetView workbookViewId=\"0\">"
        '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
        "</sheetView></sheetViews>",
        '<sheetFormatPr defaultRowHeight="18"/>',
        "<cols>",
    ]

    for index, width in enumerate(COLUMN_WIDTHS, start=1):
        lines.append(
            f'<col min="{index}" max="{index}" width="{width}" customWidth="1"/>',
        )
    lines.append("</cols>")
    lines.append("<sheetData>")

    headers = [header for header, _ in COLUMNS]
    lines.append(f'<row r="1" ht="{row_height(headers, True)}" customHeight="1">')
    for column, header in enumerate(headers, start=1):
        lines.append(cell_xml(1, column, header, style=1))
    lines.append("</row>")

    for row_index, case in enumerate(cases, start=2):
        values: list[Any] = []
        for _, key in COLUMNS:
            if key == "__index__":
                values.append(row_index - 1)
            else:
                values.append(case.get(key, ""))

        lines.append(
            f'<row r="{row_index}" ht="{row_height(values)}" customHeight="1">',
        )
        for column, ((_, key), value) in enumerate(zip(COLUMNS, values), start=1):
            style = PRIORITY_STYLES.get(clean_text(value), 0) if key == "priority" else 0
            lines.append(cell_xml(row_index, column, value, style=style))
        lines.append("</row>")

    lines.extend(
        [
            "</sheetData>",
            f'<autoFilter ref="A1:{last_ref}"/>',
            "</worksheet>",
        ],
    )
    return "\n".join(lines)


def workbook_xml(sheet_name: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        "<sheets>"
        f'<sheet name="{escape(sheet_name, quote=True)}" sheetId="1" r:id="rId1"/>'
        "</sheets>"
        "</workbook>"
    )


def workbook_rels_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet1.xml"/>'
        '<Relationship Id="rId2" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
        'Target="styles.xml"/>'
        "</Relationships>"
    )


def root_rels_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/>'
        '<Relationship Id="rId2" '
        'Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" '
        'Target="docProps/core.xml"/>'
        '<Relationship Id="rId3" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" '
        'Target="docProps/app.xml"/>'
        "</Relationships>"
    )


def content_types_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '<Override PartName="/xl/styles.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        '<Override PartName="/docProps/core.xml" '
        'ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
        '<Override PartName="/docProps/app.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
        "</Types>"
    )


def styles_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="2">
    <font><sz val="11"/><name val="Arial"/></font>
    <font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Arial"/></font>
  </fonts>
  <fills count="7">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FF2F5597"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFFFC7CE"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFFFE699"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFD9EAD3"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFE7E6E6"/></patternFill></fill>
  </fills>
  <borders count="2">
    <border><left/><right/><top/><bottom/><diagonal/></border>
    <border>
      <left style="thin"><color rgb="FFD9D9D9"/></left>
      <right style="thin"><color rgb="FFD9D9D9"/></right>
      <top style="thin"><color rgb="FFD9D9D9"/></top>
      <bottom style="thin"><color rgb="FFD9D9D9"/></bottom>
      <diagonal/>
    </border>
  </borders>
  <cellStyleXfs count="1">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
  </cellStyleXfs>
  <cellXfs count="6">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="1" applyBorder="1" applyAlignment="1">
      <alignment vertical="top" wrapText="1"/>
    </xf>
    <xf numFmtId="0" fontId="1" fillId="2" borderId="1" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1">
      <alignment horizontal="center" vertical="center" wrapText="1"/>
    </xf>
    <xf numFmtId="0" fontId="0" fillId="3" borderId="1" applyFill="1" applyBorder="1" applyAlignment="1">
      <alignment horizontal="center" vertical="center" wrapText="1"/>
    </xf>
    <xf numFmtId="0" fontId="0" fillId="4" borderId="1" applyFill="1" applyBorder="1" applyAlignment="1">
      <alignment horizontal="center" vertical="center" wrapText="1"/>
    </xf>
    <xf numFmtId="0" fontId="0" fillId="5" borderId="1" applyFill="1" applyBorder="1" applyAlignment="1">
      <alignment horizontal="center" vertical="center" wrapText="1"/>
    </xf>
    <xf numFmtId="0" fontId="0" fillId="6" borderId="1" applyFill="1" applyBorder="1" applyAlignment="1">
      <alignment horizontal="center" vertical="center" wrapText="1"/>
    </xf>
  </cellXfs>
  <cellStyles count="1">
    <cellStyle name="Normal" xfId="0" builtinId="0"/>
  </cellStyles>
</styleSheet>
"""


def app_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
        'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
        "<Application>Python</Application>"
        "</Properties>"
    )


def core_xml() -> str:
    created = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:dcmitype="http://purl.org/dc/dcmitype/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        "<dc:creator>json_test_cases_to_excel.py</dc:creator>"
        "<cp:lastModifiedBy>json_test_cases_to_excel.py</cp:lastModifiedBy>"
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{created}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{created}</dcterms:modified>'
        "</cp:coreProperties>"
    )


def write_xlsx(cases: list[dict[str, Any]], output_path: Path, sheet_name: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet_name = safe_sheet_name(sheet_name)

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types_xml())
        archive.writestr("_rels/.rels", root_rels_xml())
        archive.writestr("docProps/app.xml", app_xml())
        archive.writestr("docProps/core.xml", core_xml())
        archive.writestr("xl/workbook.xml", workbook_xml(sheet_name))
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml())
        archive.writestr("xl/styles.xml", styles_xml())
        archive.writestr("xl/worksheets/sheet1.xml", worksheet_xml(cases))


def main() -> int:
    args = parse_args()
    json_path = Path(args.json_file).expanduser().resolve()
    if not json_path.exists():
        print(f"JSON 文件不存在：{json_path}", file=sys.stderr)
        return 1

    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else json_path.with_suffix(".xlsx")
    )

    try:
        cases = load_cases(json_path)
        write_xlsx(cases, output_path, args.sheet_name)
    except Exception as exc:  # noqa: BLE001 - CLI should print concise errors.
        print(f"转换失败：{exc}", file=sys.stderr)
        return 1

    print(f"已转换 {len(cases)} 条用例：{output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
