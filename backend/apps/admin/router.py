"""后台管理路由

提供给管理员（无需密码，用户名 Yanglab）查看与导出各项测试结果及用户信息。
支持按起止日期、学校、用户名筛选，并可导出为 CSV / XLSX。
"""
import io
import os
import zipfile
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse, FileResponse
from sqlmodel import Session, select

from database import get_session
from config import UPLOAD_DIR
from apps.users.models import User
from apps.reading_fluency.models import TestSession as ReadingSession, Trial as ReadingTrial
from apps.attention_test.models import AttentionTestSession, AttentionRecord
from apps.calculation_test.models import CalculationTestSession, CalculationProblem
from apps.literacy_test.models import LiteracyTest, LiteracyAudioRecord
from apps.oral_reading_fluency.models import OralReadingFluencyTest, OralReadingAudioRecord
from apps.raven_test.models import RavenTestSession, RavenAnswer
from apps.oral_reading_fluency.service import CHARACTER_ROWS

router = APIRouter(tags=["后台管理"])

# 后端根目录（config 中 UPLOAD_DIR = <backend>/uploads）
BACKEND_DIR = Path(UPLOAD_DIR).parent


def _resolve_audio_path(stored: Optional[str]) -> Optional[Path]:
    """把数据库中存储的音频路径解析为真实存在的文件路径。

    朗读流畅性存的是 "uploads/oral_reading_fluency/xxx.mp3"（相对后端根目录），
    识字量存的是相对 UPLOAD_DIR 的路径（如 "literacy_test/xxx.mp3"）。
    """
    if not stored:
        return None
    candidates = [
        Path(stored),
        BACKEND_DIR / stored,
        Path(UPLOAD_DIR) / stored,
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None

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


# 明细（具体操作数据）注册表：key -> 配置
# model: 明细表模型；fk: 指向会话的外键属性名；order: 排序字段；metrics: [(属性, 列名)]
DETAIL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "reading_fluency": {
        "model": ReadingTrial,
        "fk": "test_session_id",
        "order": ["trial_id"],
        "metrics": [
            ("trial_id", "试题编号"),
            ("user_answer", "用户回答"),
            ("is_correct", "是否正确"),
            ("response_time", "回答时间(ms)"),
        ],
    },
    "oral_reading_fluency": {
        "model": OralReadingAudioRecord,
        "fk": "test_id",
        "order": ["round_number", "row_index"],
        "metrics": [
            ("round_number", "轮次"),
            ("row_index", "行索引"),
            ("correct_character_count", "正确字数"),
            ("total_score", "总分"),
            ("fluency_score", "流畅度"),
            ("evaluation_status", "评测状态"),
        ],
    },
    "attention_test": {
        "model": AttentionRecord,
        "fk": "test_session_id",
        "order": ["row_index", "col_index"],
        "metrics": [
            ("row_index", "行"),
            ("col_index", "列"),
            ("symbol", "符号"),
            ("is_target", "是否目标"),
            ("is_correct", "是否正确"),
            ("response_time", "响应时间(ms)"),
        ],
    },
    "calculation": {
        "model": CalculationProblem,
        "fk": "test_session_id",
        "order": ["problem_index"],
        "metrics": [
            ("problem_index", "题号"),
            ("problem_text", "题目"),
            ("problem_type", "类型"),
            ("correct_answer", "正确答案"),
            ("user_answer", "用户答案"),
            ("is_correct", "是否正确"),
            ("response_time", "回答时间(ms)"),
            ("score", "得分"),
        ],
    },
    "literacy": {
        "model": LiteracyAudioRecord,
        "fk": "test_id",
        "order": ["group_id", "id"],
        "metrics": [
            ("character", "字"),
            ("group_id", "组"),
            ("coefficient", "系数"),
            ("is_correct", "是否正确"),
            ("confidence_score", "置信度"),
            ("evaluation_status", "评测状态"),
            ("audio_duration", "时长(秒)"),
        ],
    },
    "raven": {
        "model": RavenAnswer,
        "fk": "test_session_id",
        "order": ["question_id"],
        "metrics": [
            ("question_id", "题号"),
            ("group_name", "组"),
            ("user_answer", "用户答案"),
            ("correct_answer", "正确答案"),
            ("is_correct", "是否正确"),
            ("response_time", "回答时间(ms)"),
        ],
    },
}


def _fmt(value) -> Any:
    """格式化单元格值，便于 JSON / 表格展示"""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "是" if value else "否"
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


def _query_sessions(
    session: Session,
    key: str,
    start_dt: datetime,
    end_dt: datetime,
    school: Optional[str],
    name: Optional[str],
    ids: Optional[List[int]] = None,
):
    """查询某测试类型的会话（含用户），返回 [(obj, user), ...]"""
    Model = TEST_REGISTRY[key]["model"]
    stmt = (
        select(Model, User)
        .join(User, Model.user_id == User.id)
        .where(Model.start_time >= start_dt, Model.start_time < end_dt)
    )
    if school:
        stmt = stmt.where(User.school.contains(school))  # type: ignore
    if name:
        stmt = stmt.where(User.name.contains(name))  # type: ignore
    if ids:
        stmt = stmt.where(Model.id.in_(ids))  # type: ignore
    stmt = stmt.order_by(Model.start_time.desc())  # type: ignore
    return session.exec(stmt).all()


def _common_cells(obj, user) -> Dict[str, Any]:
    return {
        "姓名": user.name,
        "学校": user.school,
        "年级": user.grade,
        "班级": user.class_number,
        "出生日期": _fmt(user.birth_date),
        "测试时间": _fmt(obj.start_time),
        "结束时间": _fmt(getattr(obj, "end_time", None)),
        "状态": _status_text(obj),
    }


def _build_dataset(
    session: Session,
    start_dt: datetime,
    end_dt: datetime,
    school: Optional[str],
    name: Optional[str],
    only_type: Optional[str] = None,
    ids: Optional[List[int]] = None,
) -> Dict[str, Dict[str, Any]]:
    """构建各测试类型的会话汇总（每个会话一行）"""
    result: Dict[str, Dict[str, Any]] = {}
    for key, cfg in TEST_REGISTRY.items():
        if only_type and only_type != "all" and key != only_type:
            continue
        metric_labels = [label for _, label in cfg["metrics"]]
        columns = _COMMON_COLUMNS + metric_labels
        rows: List[Dict[str, Any]] = []

        for obj, user in _query_sessions(session, key, start_dt, end_dt, school, name, ids):
            row = _common_cells(obj, user)
            for attr, label in cfg["metrics"]:
                row[label] = _fmt(getattr(obj, attr, None))
            # 会话 ID，供前端查看明细 / 录音、勾选导出（不作为表格列展示）
            row["__test_id__"] = obj.id
            row["__user_id__"] = user.id
            if key in ("oral_reading_fluency", "literacy"):
                row["__has_audio__"] = True
            rows.append(row)

        result[key] = {"label": cfg["label"], "columns": columns, "rows": rows}
    return result


def _detail_items(session: Session, key: str, test_id: int) -> List[Any]:
    """获取某次会话的明细条目（已排序）"""
    dcfg = DETAIL_REGISTRY[key]
    Model = dcfg["model"]
    stmt = select(Model).where(getattr(Model, dcfg["fk"]) == test_id)
    for o in dcfg["order"]:
        stmt = stmt.order_by(getattr(Model, o))  # type: ignore
    return session.exec(stmt).all()


def _build_detail_dataset(
    session: Session,
    start_dt: datetime,
    end_dt: datetime,
    school: Optional[str],
    name: Optional[str],
    only_type: Optional[str] = None,
    ids: Optional[List[int]] = None,
) -> Dict[str, Dict[str, Any]]:
    """构建宽表：通用列 + 会话汇总列 + 明细列，每条明细一行（无明细则保留汇总行）"""
    result: Dict[str, Dict[str, Any]] = {}
    for key, scfg in TEST_REGISTRY.items():
        if only_type and only_type != "all" and key != only_type:
            continue
        dcfg = DETAIL_REGISTRY[key]
        session_labels = [label for _, label in scfg["metrics"]]
        detail_labels = ["明细·" + label for _, label in dcfg["metrics"]]
        columns = _COMMON_COLUMNS + session_labels + detail_labels
        rows: List[Dict[str, Any]] = []

        for obj, user in _query_sessions(session, key, start_dt, end_dt, school, name, ids):
            base = _common_cells(obj, user)
            for attr, label in scfg["metrics"]:
                base[label] = _fmt(getattr(obj, attr, None))
            items = _detail_items(session, key, obj.id)
            if not items:
                rows.append({**base, **{dl: "" for dl in detail_labels}})
                continue
            for it in items:
                row = dict(base)
                for attr, label in dcfg["metrics"]:
                    row["明细·" + label] = _fmt(getattr(it, attr, None))
                rows.append(row)

        result[key] = {"label": scfg["label"], "columns": columns, "rows": rows}
    return result


def _parse_ids(ids: Optional[str]) -> Optional[List[int]]:
    if not ids:
        return None
    out = [int(p) for p in ids.split(",") if p.strip().isdigit()]
    return out or None


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
    scope: str = Query("summary", pattern="^(summary|detail)$", description="summary=仅记录表，detail=含明细宽表"),
    ids: Optional[str] = Query(None, description="仅导出指定会话 ID（逗号分隔），需配合具体 test_type"),
    session: Session = Depends(get_session),
):
    """导出测试结果为 CSV 或 XLSX；scope=detail 时导出含具体操作数据的宽表"""
    if test_type != "all" and test_type not in TEST_REGISTRY:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="未知的测试类型")
    try:
        start_dt, end_dt = _parse_range(start_date, end_date)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="日期格式应为 YYYY-MM-DD")

    # 勾选导出仅在指定单一测试类型时生效
    id_list = _parse_ids(ids) if test_type != "all" else None

    if scope == "detail":
        data = _build_detail_dataset(session, start_dt, end_dt, school, name, only_type=test_type, ids=id_list)
    else:
        data = _build_dataset(session, start_dt, end_dt, school, name, only_type=test_type, ids=id_list)
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
    if test_type == "all" and scope == "detail":
        # 明细宽表多类型：纵向拼接，列取并集，加测试类型列
        frames = []
        for key, ds in data.items():
            if not ds["rows"]:
                continue
            df_part = pd.DataFrame(ds["rows"], columns=ds["columns"])
            df_part.insert(0, "测试类型", ds["label"])
            frames.append(df_part)
        df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    elif test_type == "all":
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


@router.get("/detail")
async def get_detail(
    test_type: str = Query(..., description="测试类型 key"),
    test_id: int = Query(..., description="会话 ID"),
    session: Session = Depends(get_session),
):
    """在线查看某次会话的具体操作明细数据"""
    if test_type not in DETAIL_REGISTRY:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="未知的测试类型")
    cfg = TEST_REGISTRY[test_type]
    Model = cfg["model"]
    obj = session.get(Model, test_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试不存在")
    user = session.get(User, obj.user_id) if obj.user_id else None

    dcfg = DETAIL_REGISTRY[test_type]
    columns = [label for _, label in dcfg["metrics"]]
    rows: List[Dict[str, Any]] = []
    for it in _detail_items(session, test_type, test_id):
        rows.append({label: _fmt(getattr(it, attr, None)) for attr, label in dcfg["metrics"]})

    return {
        "success": True,
        "label": cfg["label"],
        "user": {
            "name": user.name if user else "",
            "school": user.school if user else "",
            "grade": user.grade if user else "",
            "class_number": user.class_number if user else "",
        },
        "columns": columns,
        "rows": rows,
        "total": len(rows),
    }


# ---------------------------------------------------------------------------
# 录音相关：朗读流畅性 / 识字量 在线播放、查看题目、下载
# ---------------------------------------------------------------------------

def _oral_items(session: Session, test_id: int) -> List[Dict[str, Any]]:
    """朗读流畅性某次测试的全部录音条目"""
    records = session.exec(
        select(OralReadingAudioRecord)
        .where(OralReadingAudioRecord.test_id == test_id)
        .order_by(OralReadingAudioRecord.round_number, OralReadingAudioRecord.row_index)  # type: ignore
    ).all()
    items = []
    for r in records:
        row_chars = CHARACTER_ROWS[r.row_index] if 0 <= r.row_index < len(CHARACTER_ROWS) else ""
        items.append({
            "record_id": r.id,
            "title": f"第{r.round_number}轮 · 第{r.row_index + 1}行",
            "stimulus": row_chars,
            "has_file": _resolve_audio_path(r.audio_file_path) is not None,
            "audio_url": f"/api/admin/audio/file?test=oral&record_id={r.id}",
            "evaluation_status": r.evaluation_status,
            "total_score": r.total_score,
            "correct_character_count": r.correct_character_count,
        })
    return items


def _literacy_items(session: Session, test_id: int) -> List[Dict[str, Any]]:
    """识字量某次测试的全部录音条目"""
    records = session.exec(
        select(LiteracyAudioRecord)
        .where(LiteracyAudioRecord.test_id == test_id)
        .order_by(LiteracyAudioRecord.group_id, LiteracyAudioRecord.id)  # type: ignore
    ).all()
    items = []
    for r in records:
        items.append({
            "record_id": r.id,
            "title": r.character,
            "stimulus": r.character,
            "group_id": r.group_id,
            "has_file": _resolve_audio_path(r.audio_file_path) is not None,
            "audio_url": f"/api/admin/audio/file?test=literacy&record_id={r.id}",
            "evaluation_status": r.evaluation_status,
            "is_correct": r.is_correct,
            "confidence_score": r.confidence_score,
        })
    return items


@router.get("/audio/recordings")
async def get_recordings(
    test: str = Query(..., pattern="^(oral|literacy)$"),
    test_id: int = Query(...),
    session: Session = Depends(get_session),
):
    """获取某次朗读流畅性/识字量测试的全部录音条目（含题目，用于在线播放与评分）"""
    if test == "oral":
        test_obj = session.get(OralReadingFluencyTest, test_id)
        items = _oral_items(session, test_id)
        # 朗读流畅性题目为全部字行
        questions = list(CHARACTER_ROWS)
    else:
        test_obj = session.get(LiteracyTest, test_id)
        items = _literacy_items(session, test_id)
        questions = [it["stimulus"] for it in items]
    if not test_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试不存在")

    user = session.get(User, test_obj.user_id) if test_obj.user_id else None
    return {
        "success": True,
        "test": test,
        "test_id": test_id,
        "user": {
            "name": user.name if user else "",
            "school": user.school if user else "",
            "grade": user.grade if user else "",
            "class_number": user.class_number if user else "",
        },
        "questions": questions,
        "items": items,
        "total": len(items),
    }


def _get_audio_record(session: Session, test: str, record_id: int):
    if test == "oral":
        return session.get(OralReadingAudioRecord, record_id)
    return session.get(LiteracyAudioRecord, record_id)


@router.get("/audio/file")
async def get_audio_file(
    test: str = Query(..., pattern="^(oral|literacy)$"),
    record_id: int = Query(...),
    session: Session = Depends(get_session),
):
    """在线播放/下载单条录音文件"""
    record = _get_audio_record(session, test, record_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="录音记录不存在")
    path = _resolve_audio_path(record.audio_file_path)
    if not path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="录音文件不存在")
    media = "audio/mpeg" if path.suffix.lower() == ".mp3" else "application/octet-stream"
    return FileResponse(str(path), media_type=media, filename=path.name)


@router.get("/audio/download-all")
async def download_all_audio(
    test: str = Query(..., pattern="^(oral|literacy)$"),
    test_id: int = Query(...),
    session: Session = Depends(get_session),
):
    """打包下载某次测试的全部录音（ZIP）"""
    if test == "oral":
        test_obj = session.get(OralReadingFluencyTest, test_id)
        records = session.exec(
            select(OralReadingAudioRecord).where(OralReadingAudioRecord.test_id == test_id)
        ).all()
        def arcname(r):
            return f"round{r.round_number}_row{r.row_index + 1}_{Path(r.audio_file_path or '').name}"
    else:
        test_obj = session.get(LiteracyTest, test_id)
        records = session.exec(
            select(LiteracyAudioRecord).where(LiteracyAudioRecord.test_id == test_id)
        ).all()
        def arcname(r):
            base = Path(r.audio_file_path or "").name or f"record_{r.id}.mp3"
            return f"{r.group_id}_{r.character}_{base}"

    if not test_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试不存在")

    user = session.get(User, test_obj.user_id) if test_obj.user_id else None
    buf = io.BytesIO()
    count = 0
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for r in records:
            path = _resolve_audio_path(r.audio_file_path)
            if path:
                zf.write(str(path), arcname(r))
                count += 1
    if count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="该测试没有可下载的录音文件")
    buf.seek(0)
    uname = (user.name if user else "user").replace("/", "_")
    filename = f"recordings_{test}_{uname}_{test_id}.zip"
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
