from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List, Dict, Any

from database import get_session
from .models import (
    CalculationProblem,
    CalculationTestSession,
    ProblemData,
    BatchProblemData,
    TestSessionCreate,
    TestSessionUpdate,
    TestSessionResponse,
    ResultResponse,
)
from .service import (
    create_test_session,
    get_test_session,
    update_test_session,
    list_user_test_sessions,
    complete_test_session,
    save_problem,
    save_batch_problems,
    get_session_problems,
    get_test_session_results,
    get_grade_performance_analysis,
    get_fixed_problems_for_grade,
)

# 创建路由
router = APIRouter(tags=["计算流畅性测试"])


@router.post("/sessions", response_model=TestSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session_route(
    test_session_data: TestSessionCreate, session: Session = Depends(get_session)
):
    """创建新的测试会话"""
    try:
        test_session = create_test_session(session, test_session_data)
        return test_session
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"创建测试会话失败: {str(e)}"
        )


@router.get("/sessions/{test_session_id}", response_model=TestSessionResponse)
async def get_session_route(test_session_id: int, session: Session = Depends(get_session)):
    """获取测试会话信息"""
    test_session = get_test_session(session, test_session_id)
    if not test_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试会话不存在")
    return test_session


@router.put("/sessions/{test_session_id}", response_model=TestSessionResponse)
async def update_session_route(
    test_session_id: int, update_data: TestSessionUpdate, session: Session = Depends(get_session)
):
    """更新测试会话信息"""
    test_session = update_test_session(session, test_session_id, update_data)
    if not test_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试会话不存在")
    return test_session


@router.get("/users/{user_id}/sessions", response_model=List[TestSessionResponse])
async def list_user_sessions_route(user_id: int, session: Session = Depends(get_session)):
    """获取用户的所有测试会话"""
    return list_user_test_sessions(session, user_id)


@router.post("/sessions/{test_session_id}/complete", response_model=TestSessionResponse)
async def complete_session_route(test_session_id: int, session: Session = Depends(get_session)):
    """完成测试会话"""
    test_session = complete_test_session(session, test_session_id)
    if not test_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试会话不存在")
    return test_session


@router.post("/sessions/{test_session_id}/problems", status_code=status.HTTP_201_CREATED)
async def save_problem_route(
    test_session_id: int, problem_data: ProblemData, session: Session = Depends(get_session)
):
    """保存计算题目记录"""
    try:
        problem = save_problem(session, test_session_id, problem_data)
        return {"message": "数据保存成功", "id": problem.id}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"保存题目数据失败: {str(e)}"
        )


@router.get("/sessions/{test_session_id}/problems")
async def get_session_problems_route(test_session_id: int, session: Session = Depends(get_session)):
    """获取测试会话中的所有计算题目记录"""
    test_session = get_test_session(session, test_session_id)
    if not test_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试会话不存在")
    return get_session_problems(session, test_session_id)


@router.get("/sessions/{test_session_id}/results", response_model=Dict[str, Any])
async def get_session_results_route(test_session_id: int, session: Session = Depends(get_session)):
    """获取测试会话的结果"""
    results = get_test_session_results(session, test_session_id)
    if not results:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试会话不存在")
    return results


@router.post("/sessions/{test_session_id}/problems-batch", status_code=status.HTTP_201_CREATED)
async def save_batch_problems_route(
    test_session_id: int, batch_data: BatchProblemData, session: Session = Depends(get_session)
):
    """批量保存计算题目记录"""
    try:
        results = save_batch_problems(session, test_session_id, batch_data)
        return {"message": "批量数据保存成功", "saved_count": len(results)}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"保存批量题目数据失败: {str(e)}"
        )


@router.get("/users/{user_id}/grades/{grade_level}/analysis", response_model=Dict[str, Any])
async def get_grade_analysis_route(
    user_id: int, grade_level: int, session: Session = Depends(get_session)
):
    """获取用户在特定年级的所有测试表现分析"""
    try:
        analysis = get_grade_performance_analysis(session, user_id, grade_level)
        return analysis
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"获取性能分析失败: {str(e)}"
        )


@router.get("/sessions/{test_session_id}/detailed-analysis", response_model=Dict[str, Any])
async def get_detailed_analysis_route(
    test_session_id: int, session: Session = Depends(get_session)
):
    """获取测试会话的详细分析报告"""
    try:
        # 获取基本结果
        results = get_test_session_results(session, test_session_id)
        if not results:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试会话不存在")
        
        # 添加详细分析
        stats = results["stats"]
        detailed_analysis = {
            "basicStats": {
                "totalProblems": stats["totalProblems"],
                "correctProblems": stats["correctProblems"],
                "accuracy": stats["accuracy"],
                "completionRate": stats["completionRate"]
            },
            "typeAnalysis": stats.get("problemTypeStats", {}),
            "difficultyAnalysis": stats.get("difficultyAnalysis", {}),
            "errorAnalysis": stats.get("errorAnalysis", {}),
            "speedAnalysis": stats.get("speedAnalysis", {}),
            "specialAnalysis": {
                "fractionAnalysis": stats.get("fractionAnalysis", {}),
                "multiplicationAnalysis": stats.get("multiplicationAnalysis", {})
            },
            "recommendations": generate_recommendations(results)
        }
        
        return detailed_analysis
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取详细分析失败: {str(e)}"
        )


def generate_recommendations(results: Dict[str, Any]) -> List[str]:
    """根据测试结果生成学习建议"""
    recommendations = []
    stats = results.get("stats", {})
    session_data = results.get("session", {})
    
    accuracy = stats.get("accuracy", 0)
    grade_level = getattr(session_data, "grade_level", 4)
    
    # 根据正确率给出建议
    if accuracy < 60:
        recommendations.append("建议加强基础计算练习，特别是加减法运算")
    elif accuracy < 80:
        recommendations.append("基础计算能力尚可，建议多做练习提高熟练度")
    else:
        recommendations.append("计算能力较强，可以尝试更高难度的题目")
    
    # 根据题型表现给出建议
    problem_types = stats.get("problemTypeStats", {})
    for type_name, type_stats in problem_types.items():
        type_accuracy = type_stats.get("accuracy", 0)
        if type_accuracy < 70:
            if type_name == "fractionAddSub":
                recommendations.append("分数加减法较弱，建议加强通分和化简练习")
            elif "Mult" in type_name:
                recommendations.append("乘法运算需要加强，建议背诵乘法口诀表")
            elif "AddSub" in type_name:
                recommendations.append("加减法运算需要练习，注意计算准确性")
    
    # 根据速度分析给出建议
    avg_time = stats.get("averageResponseTime", 0)
    if avg_time > 30:  # 假设30秒以上较慢
        recommendations.append("答题速度较慢，建议多做速算练习提高计算速度")
    
    # 根据一致性给出建议
    consistency = stats.get("speedAnalysis", {}).get("consistencyScore", 100)
    if consistency < 70:
        recommendations.append("答题速度波动较大，建议加强专注力训练")
    
    if not recommendations:
        recommendations.append("表现优秀，继续保持！")
    
    return recommendations


@router.get("/grades/{grade_level}/problems", response_model=List[Dict[str, Any]])
async def get_grade_problems_route(grade_level: int):
    """获取指定年级的固定题目"""
    try:
        problems = get_fixed_problems_for_grade(grade_level)
        if not problems:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"未找到年级 {grade_level} 的题目"
            )
        return problems
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取年级 {grade_level} 题目失败: {str(e)}"
        )