"""后台管理路由

提供给管理员（无需密码，用户名 Yanglab）查看与导出各项测试结果及用户信息。
支持按起止日期、学校、用户名筛选，并可导出为 CSV / XLSX。
"""
import io
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from database import get_session
from apps.users.models import User
from apps.reading_fluency.models import TestSession as ReadingSession
from apps.attention_test.models import AttentionTestSession
from apps.calculation_test.models import CalculationTestSession
from apps.literacy_test.models import LiteracyTest
from apps.oral_reading_fluency.models import OralReadingFluencyTest
from apps.raven_test.models import RavenTestSession

router = APIRouter(tags=["后台管理"])

# 通用用户列（所有测试共有）
_COMMON_COLUMNS = ["姓名", "学校", "年级", "班级", "出生日期", "测试时间", "结束时间", "状态"]


def _status_text(obj) -> str:
    """统一的状态描述"""
    if hasattr(obj, "is_completed"):
        return "已完成" if getattr(obj, "is_completed") else "未完成"
    # oral / literacy 使用字符串 status
    val = getattr(obj, "status", None)
    if val is None:
        return ""
    return getattr(val, "value", str(val))


# 测试类型注册表：key -> 配置
# metrics: [(模型属性, 列名)]
TEST_REGISTRY: Dict[str, Dict[str, Any]] = {
    "reading_fluency": {
        "label": "阅读流畅性",
        "model": ReadingSession,
        "metrics": [
            ("level", "级别"),
            ("total_questions", "总题数"),
            ("correct_count", "正确数"),
            ("progress", "已完成数"),
            ("total_time_seconds", "用时(秒)"),
        ],
    },
    "oral_reading_fluency": {
        "label": "朗读流畅性",
        "model": OralReadingFluencyTest,
        "metrics": [
            ("round1_character_count", "第一轮字数"),
            ("round1_duration", "第一轮用时(秒)"),
            ("round2_character_count", "第二轮字数"),
            ("round2_duration", "第二轮用时(秒)"),
            ("average_score", "平均(字/分)"),
            ("evaluation_status", "评测状态"),
        ],
    },
    "attention_test": {
        "label": "注意力筛查",
        "model": AttentionTestSession,
        "metrics": [
            ("target_symbol", "目标符号"),
            ("correct_count", "正确点击"),
            ("incorrect_count", "错误点击"),
            ("missed_count", "遗漏数"),
            ("total_score", "得分"),
            ("total_time_seconds", "用时(秒)"),
        ],
    },
    "calculation": {
        "label": "计算流畅性",
        "model": CalculationTestSession,
        "metrics": [
            ("grade_level", "年级水平"),
            ("total_questions", "总题数"),
            ("correct_count", "正确数"),
            ("total_score", "得分"),
            ("max_score", "满分"),
            ("total_time_seconds", "用时(秒)"),
        ],
    },
    "literacy": {
        "label": "识字量",
        "model": LiteracyTest,
        "metrics": [
            ("total_characters", "总字数"),
            ("correct_characters", "正确字数"),
            ("total_score", "得分"),
            ("evaluation_status", "评测状态"),
        ],
    },
    "raven": {
        "label": "瑞文智力",
        "model": RavenTestSession,
        "metrics": [
            ("raw_score", "原始分"),
            ("percentile", "百分位"),
            ("z_score", "Z分数"),
            ("iq", "智商"),
            ("user_age", "年龄"),
            ("total_time_seconds", "用时(秒)"),
        ],
    },
}


def _fmt(value) -> Any:
    """格式化单元格值，便于 JSON / 表格展示"""
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return value


def _parse_range(start_date: Optional[str], end_date: Optional[str]):
    """解析起止日期，默认最近 1 天。end 包含当天整天。"""
    now = datetime.now()
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
    else:
        end_dt = now
    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    else:
        start_dt = end_dt - timedelta(days=1)
    return start_dt, end_dt


def _build_dataset(
    session: Session,
    start_dt: datetime,
    end_dt: datetime,
    school: Optional[str],
    name: Optional[str],
    only_type: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    """构建各测试类型的列与行数据"""
    result: Dict[str, Dict[str, Any]] = {}
    for key, cfg in TEST_REGISTRY.items():
        if only_type and only_type != "all" and key != only_type:
            continue
        Model = cfg["model"]
        stmt = (
            select(Model, User)
            .join(User, Model.user_id == User.id)
            .where(Model.start_time >= start_dt, Model.start_time < end_dt)
        )
        if school:
            stmt = stmt.where(User.school.contains(school))  # type: ignore
        if name:
            stmt = stmt.where(User.name.contains(name))  # type: ignore
        stmt = stmt.order_by(Model.start_time.desc())  # type: ignore

        metric_labels = [label for _, label in cfg["metrics"]]
        columns = _COMMON_COLUMNS + metric_labels
        rows: List[Dict[str, Any]] = []

        for obj, user in session.exec(stmt).all():
            row = {
                "姓名": user.name,
                "学校": user.school,
                "年级": user.grade,
                "班级": user.class_number,
                "出生日期": _fmt(user.birth_date),
                "测试时间": _fmt(obj.start_time),
                "结束时间": _fmt(getattr(obj, "end_time", None)),
                "状态": _status_text(obj),
            }
            for attr, label in cfg["metrics"]:
                row[label] = _fmt(getattr(obj, attr, None))
            rows.append(row)

        result[key] = {"label": cfg["label"], "columns": columns, "rows": rows}
    return result


@router.get("/results")
async def get_results(
    start_date: Optional[str] = Query(None, description="起始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    school: Optional[str] = Query(None, description="按学校筛选（模糊匹配）"),
    name: Optional[str] = Query(None, description="按用户名筛选（模糊匹配）"),
    session: Session = Depends(get_session),
):
    """在线查看各项测试结果"""
    try:
        start_dt, end_dt = _parse_range(start_date, end_date)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="日期格式应为 YYYY-MM-DD")

    data = _build_dataset(session, start_dt, end_dt, school, name)
    total = sum(len(v["rows"]) for v in data.values())
    return {
        "success": True,
        "range": {"start": start_dt.strftime("%Y-%m-%d %H:%M:%S"), "end": end_dt.strftime("%Y-%m-%d %H:%M:%S")},
        "total": total,
        "tests": data,
    }


@router.get("/export")
async def export_results(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    school: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    format: str = Query("xlsx", pattern="^(csv|xlsx)$"),
    test_type: str = Query("all", description="测试类型 key，或 all 表示全部"),
    session: Session = Depends(get_session),
):
    """导出测试结果为 CSV 或 XLSX"""
    if test_type != "all" and test_type not in TEST_REGISTRY:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="未知的测试类型")
    try:
        start_dt, end_dt = _parse_range(start_date, end_date)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="日期格式应为 YYYY-MM-DD")

    data = _build_dataset(session, start_dt, end_dt, school, name, only_type=test_type)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    if format == "xlsx":
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            wrote_any = False
            for key, ds in data.items():
                df = pd.DataFrame(ds["rows"], columns=ds["columns"])
                sheet = ds["label"][:31]
                df.to_excel(writer, sheet_name=sheet, index=False)
                wrote_any = True
            if not wrote_any:
                pd.DataFrame().to_excel(writer, sheet_name="无数据", index=False)
        buf.seek(0)
        filename = f"test_results_{test_type}_{ts}.xlsx"
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    # CSV
    if test_type == "all":
        # 合并为长格式：通用列 + 测试类型 + 结果摘要
        records: List[Dict[str, Any]] = []
        for key, ds in data.items():
            metric_cols = [c for c in ds["columns"] if c not in _COMMON_COLUMNS]
            for row in ds["rows"]:
                rec = {c: row.get(c, "") for c in _COMMON_COLUMNS}
                rec = {"测试类型": ds["label"], **rec}
                summary = "; ".join(
                    f"{c}:{row.get(c, '')}" for c in metric_cols if row.get(c, "") != ""
                )
                rec["结果摘要"] = summary
                records.append(rec)
        df = pd.DataFrame(records, columns=["测试类型", *_COMMON_COLUMNS, "结果摘要"])
    else:
        ds = data[test_type]
        df = pd.DataFrame(ds["rows"], columns=ds["columns"])

    csv_bytes = df.to_csv(index=False).encode("utf-8-sig")  # BOM 兼容 Excel 中文
    filename = f"test_results_{test_type}_{ts}.csv"
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
