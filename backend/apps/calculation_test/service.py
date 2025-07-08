from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlmodel import Session, select
import statistics

from logger_config import logger
from apps.users.models import User
from .models import (
    CalculationTestSession,
    CalculationProblem,
    TestSessionCreate,
    TestSessionUpdate,
    ProblemData,
    BatchProblemData,
)


def create_test_session(
    session: Session, test_session_data: TestSessionCreate
) -> CalculationTestSession:
    """创建新的计算流畅性测试会话"""
    # 检查用户是否存在
    user = session.get(User, test_session_data.user_id)
    if not user:
        raise ValueError(f"用户不存在: ID={test_session_data.user_id}")

    # 创建测试会话
    test_session = CalculationTestSession(
        user_id=test_session_data.user_id,
        grade_level=test_session_data.grade_level,
        total_questions=test_session_data.total_questions,
        max_score=test_session_data.total_questions,  # 最高可能得分等于总题目数
        start_time=datetime.now(),
    )

    session.add(test_session)
    session.commit()
    session.refresh(test_session)

    logger.info(
        f"为用户 {user.name} 创建计算流畅性测试会话，ID: {test_session.id}, 年级: {test_session.grade_level}"
    )
    return test_session


def get_test_session(session: Session, test_session_id: int) -> Optional[CalculationTestSession]:
    """获取测试会话信息"""
    return session.get(CalculationTestSession, test_session_id)


def update_test_session(
    session: Session, test_session_id: int, update_data: TestSessionUpdate
) -> Optional[CalculationTestSession]:
    """更新测试会话信息"""
    # 获取测试会话
    test_session = session.get(CalculationTestSession, test_session_id)
    if not test_session:
        return None

    # 更新字段
    update_dict = update_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(test_session, key, value)

    # 如果已完成且未设置结束时间，自动设置
    if update_data.is_completed and not test_session.end_time:
        test_session.end_time = datetime.now()
        # 计算总用时（秒）
        delta = test_session.end_time - test_session.start_time
        test_session.total_time_seconds = int(delta.total_seconds())

    session.add(test_session)
    session.commit()
    session.refresh(test_session)

    return test_session


def list_user_test_sessions(session: Session, user_id: int) -> List[CalculationTestSession]:
    """获取用户的所有测试会话"""
    query = select(CalculationTestSession).where(CalculationTestSession.user_id == user_id)
    return list(session.exec(query).all())


def complete_test_session(session: Session, test_session_id: int) -> Optional[CalculationTestSession]:
    """完成测试会话"""
    test_session = session.get(CalculationTestSession, test_session_id)
    if not test_session:
        return None

    # 标记为完成并设置结束时间
    test_session.is_completed = True
    test_session.end_time = datetime.now()

    # 计算总用时（秒）
    delta = test_session.end_time - test_session.start_time
    test_session.total_time_seconds = int(delta.total_seconds())

    # 计算总分（每道正确题得1分）
    query = select(CalculationProblem).where(
        CalculationProblem.test_session_id == test_session_id,
        CalculationProblem.is_correct == True
    )
    correct_problems = session.exec(query).all()
    test_session.total_score = len(correct_problems)

    session.add(test_session)
    session.commit()
    session.refresh(test_session)

    return test_session


def save_problem(
    session: Session, test_session_id: int, problem_data: ProblemData
) -> CalculationProblem:
    """保存计算题目记录"""
    # 检查会话是否存在
    test_session = session.get(CalculationTestSession, test_session_id)
    if not test_session:
        raise ValueError(f"测试会话不存在: ID={test_session_id}")

    # 检查用户是否存在
    user = session.get(User, problem_data.user_id)
    if not user:
        raise ValueError(f"用户不存在: ID={problem_data.user_id}")

    # 验证用户答案是否正确
    is_correct = problem_data.user_answer == problem_data.correct_answer
    
    # 计算得分: 正确为1分，错误或未答为0分
    score = 1 if is_correct else 0

    # 创建计算题目记录
    problem = CalculationProblem(
        user_id=problem_data.user_id,
        test_session_id=test_session_id,
        problem_index=problem_data.problem_index,
        problem_text=problem_data.problem_text,
        correct_answer=problem_data.correct_answer,
        user_answer=problem_data.user_answer,
        is_correct=is_correct,
        response_time=problem_data.response_time,
        score=score,
    )

    session.add(problem)

    # 更新测试会话进度和正确数量
    test_session.progress += 1
    if is_correct:
        test_session.correct_count += 1
        test_session.total_score += score  # 更新总分

    session.add(test_session)
    session.commit()
    session.refresh(problem)

    return problem


def get_session_problems(session: Session, test_session_id: int) -> List[CalculationProblem]:
    """获取测试会话中的所有计算题目记录"""
    query = (
        select(CalculationProblem)
        .where(CalculationProblem.test_session_id == test_session_id)
        .order_by(CalculationProblem.problem_index)
    )

    return list(session.exec(query).all())


def get_test_session_results(session: Session, test_session_id: int) -> Dict[str, Any]:
    """获取单次测试会话的结果"""
    # 获取测试会话
    test_session = session.get(CalculationTestSession, test_session_id)
    if not test_session:
        return None

    # 获取用户
    user = session.get(User, test_session.user_id) if test_session.user_id else None

    # 获取所有计算题目记录
    problems = get_session_problems(session, test_session_id)

    # 初始化统计数据
    total_response_time = sum(p.response_time for p in problems if p.response_time)
    avg_response_time = total_response_time / max(len(problems), 1)
    
    stats = {
        "totalProblems": len(problems),
        "completedProblems": test_session.progress,
        "correctProblems": test_session.correct_count,
        "totalScore": test_session.total_score,
        "maxPossibleScore": test_session.max_score,
        "scorePercentage": test_session.score_percentage,
        "accuracy": test_session.accuracy,
        "completionRate": test_session.completion_rate,
        "totalTimeSeconds": test_session.total_time_seconds,
        "averageResponseTime": avg_response_time,
        "problemTypeStats": {},
        "difficultyAnalysis": {},
        "errorAnalysis": {},
        "speedAnalysis": {}
    }
    
    # 根据年级分析题型
    if test_session.grade_level == 1:
        # 一年级: 加法题和减法题
        addition_problems = [p for p in problems if "+" in p.problem_text]
        subtraction_problems = [p for p in problems if "-" in p.problem_text]
        
        stats["problemTypeStats"] = {
            "addition": {
                "total": len(addition_problems),
                "completed": sum(1 for p in addition_problems if p.user_answer is not None),
                "correct": sum(1 for p in addition_problems if p.is_correct),
                "accuracy": sum(1 for p in addition_problems if p.is_correct) / max(len(addition_problems), 1) * 100
            },
            "subtraction": {
                "total": len(subtraction_problems),
                "completed": sum(1 for p in subtraction_problems if p.user_answer is not None),
                "correct": sum(1 for p in subtraction_problems if p.is_correct),
                "accuracy": sum(1 for p in subtraction_problems if p.is_correct) / max(len(subtraction_problems), 1) * 100
            }
        }
    elif test_session.grade_level == 2:
        # 二年级: 两数加减法和三数加减法
        two_num_problems = [p for p in problems if p.problem_text.count("+") + p.problem_text.count("-") == 1]
        three_num_problems = [p for p in problems if p.problem_text.count("+") + p.problem_text.count("-") == 2]
        
        stats["problemTypeStats"] = {
            "twoNumbers": {
                "total": len(two_num_problems),
                "completed": sum(1 for p in two_num_problems if p.user_answer is not None),
                "correct": sum(1 for p in two_num_problems if p.is_correct),
                "accuracy": sum(1 for p in two_num_problems if p.is_correct) / max(len(two_num_problems), 1) * 100
            },
            "threeNumbers": {
                "total": len(three_num_problems),
                "completed": sum(1 for p in three_num_problems if p.user_answer is not None),
                "correct": sum(1 for p in three_num_problems if p.is_correct),
                "accuracy": sum(1 for p in three_num_problems if p.is_correct) / max(len(three_num_problems), 1) * 100
            }
        }
    elif test_session.grade_level == 3:
        # 三年级: 分类统计
        # 简化统计，只按照操作数的位数分类
        stats["problemTypeStats"] = {
            "twoDigitOperations": {
                "total": sum(1 for p in problems if p.problem_index <= 10),
                "completed": sum(1 for p in problems if p.problem_index <= 10 and p.user_answer is not None),
                "correct": sum(1 for p in problems if p.problem_index <= 10 and p.is_correct),
                "accuracy": sum(1 for p in problems if p.problem_index <= 10 and p.is_correct) / 
                            max(sum(1 for p in problems if p.problem_index <= 10), 1) * 100
            },
            "threeDigitOperations": {
                "total": sum(1 for p in problems if 10 < p.problem_index <= 30),
                "completed": sum(1 for p in problems if 10 < p.problem_index <= 30 and p.user_answer is not None),
                "correct": sum(1 for p in problems if 10 < p.problem_index <= 30 and p.is_correct),
                "accuracy": sum(1 for p in problems if 10 < p.problem_index <= 30 and p.is_correct) / 
                            max(sum(1 for p in problems if 10 < p.problem_index <= 30), 1) * 100
            },
            "threeDigitThreeNumbers": {
                "total": sum(1 for p in problems if p.problem_index > 30),
                "completed": sum(1 for p in problems if p.problem_index > 30 and p.user_answer is not None),
                "correct": sum(1 for p in problems if p.problem_index > 30 and p.is_correct),
                "accuracy": sum(1 for p in problems if p.problem_index > 30 and p.is_correct) / 
                            max(sum(1 for p in problems if p.problem_index > 30), 1) * 100
            }
        }
    elif test_session.grade_level == 4:
        # 四年级: 两位数加减法、两位数乘法、分数加减法、三位数乘两位数
        two_digit_add_sub = [p for p in problems if p.problem_index <= 10]
        two_digit_mult = [p for p in problems if 10 < p.problem_index <= 20]
        fraction_add_sub = [p for p in problems if 20 < p.problem_index <= 30]
        three_digit_mult = [p for p in problems if p.problem_index > 30]
        
        stats["problemTypeStats"] = {
            "twoDigitAddSub": {
                "total": len(two_digit_add_sub),
                "completed": sum(1 for p in two_digit_add_sub if p.user_answer is not None),
                "correct": sum(1 for p in two_digit_add_sub if p.is_correct),
                "accuracy": sum(1 for p in two_digit_add_sub if p.is_correct) / max(len(two_digit_add_sub), 1) * 100,
                "avgResponseTime": sum(p.response_time for p in two_digit_add_sub if p.response_time) / max(len(two_digit_add_sub), 1),
                "errors": [p for p in two_digit_add_sub if not p.is_correct and p.user_answer is not None]
            },
            "twoDigitMult": {
                "total": len(two_digit_mult),
                "completed": sum(1 for p in two_digit_mult if p.user_answer is not None),
                "correct": sum(1 for p in two_digit_mult if p.is_correct),
                "accuracy": sum(1 for p in two_digit_mult if p.is_correct) / max(len(two_digit_mult), 1) * 100,
                "avgResponseTime": sum(p.response_time for p in two_digit_mult if p.response_time) / max(len(two_digit_mult), 1),
                "errors": [p for p in two_digit_mult if not p.is_correct and p.user_answer is not None]
            },
            "fractionAddSub": {
                "total": len(fraction_add_sub),
                "completed": sum(1 for p in fraction_add_sub if p.user_answer is not None),
                "correct": sum(1 for p in fraction_add_sub if p.is_correct),
                "accuracy": sum(1 for p in fraction_add_sub if p.is_correct) / max(len(fraction_add_sub), 1) * 100,
                "avgResponseTime": sum(p.response_time for p in fraction_add_sub if p.response_time) / max(len(fraction_add_sub), 1),
                "errors": [p for p in fraction_add_sub if not p.is_correct and p.user_answer is not None]
            },
            "threeDigitMult": {
                "total": len(three_digit_mult),
                "completed": sum(1 for p in three_digit_mult if p.user_answer is not None),
                "correct": sum(1 for p in three_digit_mult if p.is_correct),
                "accuracy": sum(1 for p in three_digit_mult if p.is_correct) / max(len(three_digit_mult), 1) * 100,
                "avgResponseTime": sum(p.response_time for p in three_digit_mult if p.response_time) / max(len(three_digit_mult), 1),
                "errors": [p for p in three_digit_mult if not p.is_correct and p.user_answer is not None]
            }
        }
        
        # 四年级特殊分析
        # 分数运算专项分析
        fraction_problems = [p for p in problems if "/" in p.problem_text]
        if fraction_problems:
            stats["fractionAnalysis"] = {
                "total": len(fraction_problems),
                "correct": sum(1 for p in fraction_problems if p.is_correct),
                "accuracy": sum(1 for p in fraction_problems if p.is_correct) / len(fraction_problems) * 100,
                "commonErrors": analyze_fraction_errors(fraction_problems)
            }
        
        # 乘法运算专项分析
        mult_problems = [p for p in problems if "×" in p.problem_text]
        if mult_problems:
            stats["multiplicationAnalysis"] = {
                "total": len(mult_problems),
                "correct": sum(1 for p in mult_problems if p.is_correct),
                "accuracy": sum(1 for p in mult_problems if p.is_correct) / len(mult_problems) * 100,
                "avgResponseTime": sum(p.response_time for p in mult_problems if p.response_time) / len(mult_problems)
            }
    elif test_session.grade_level == 5:
        # 五年级: 小数运算
        stats["problemTypeStats"] = {
            "decimal": {
                "total": len(problems),
                "completed": sum(1 for p in problems if p.user_answer is not None),
                "correct": sum(1 for p in problems if p.is_correct),
                "accuracy": sum(1 for p in problems if p.is_correct) / max(len(problems), 1) * 100
            }
        }
    
    # 添加难度分析
    if problems:
        # 按题目位置分析难度（前、中、后）
        total_problems = len(problems)
        first_third = problems[:total_problems//3]
        second_third = problems[total_problems//3:2*total_problems//3]
        last_third = problems[2*total_problems//3:]
        
        stats["difficultyAnalysis"] = {
            "firstThird": {
                "accuracy": sum(1 for p in first_third if p.is_correct) / max(len(first_third), 1) * 100,
                "avgResponseTime": sum(p.response_time for p in first_third if p.response_time) / max(len(first_third), 1)
            },
            "secondThird": {
                "accuracy": sum(1 for p in second_third if p.is_correct) / max(len(second_third), 1) * 100,
                "avgResponseTime": sum(p.response_time for p in second_third if p.response_time) / max(len(second_third), 1)
            },
            "lastThird": {
                "accuracy": sum(1 for p in last_third if p.is_correct) / max(len(last_third), 1) * 100,
                "avgResponseTime": sum(p.response_time for p in last_third if p.response_time) / max(len(last_third), 1)
            }
        }
        
        # 错误分析
        error_problems = [p for p in problems if not p.is_correct and p.user_answer is not None]
        stats["errorAnalysis"] = {
            "totalErrors": len(error_problems),
            "errorRate": len(error_problems) / max(len(problems), 1) * 100,
            "errorsByType": analyze_error_patterns(error_problems),
            "commonMistakes": get_common_mistakes(error_problems)
        }
        
        # 速度分析
        response_times = [p.response_time for p in problems if p.response_time and p.response_time > 0]
        if response_times:
            stats["speedAnalysis"] = {
                "fastest": min(response_times),
                "slowest": max(response_times),
                "median": sorted(response_times)[len(response_times)//2],
                "consistencyScore": calculate_consistency_score(response_times)
            }
    
    # 构建结果
    results = {
        "user": user,
        "session": test_session,
        "problems": problems,
        "stats": stats,
    }

    return results


def save_batch_problems(
    session: Session, test_session_id: int, batch_data: BatchProblemData
) -> List[CalculationProblem]:
    """批量保存计算题目记录"""
    # 检查会话是否存在
    test_session = session.get(CalculationTestSession, test_session_id)
    if not test_session:
        raise ValueError(f"测试会话不存在: ID={test_session_id}")

    # 检查用户是否存在
    user = session.get(User, batch_data.user_id)
    if not user:
        raise ValueError(f"用户不存在: ID={batch_data.user_id}")

    saved_problems = []
    total_correct = 0
    total_score = 0

    # 处理每个题目
    for problem_data in batch_data.problems:
        # 验证用户答案是否正确
        user_answer = problem_data.get('userAnswer')
        correct_answer = problem_data.get('correctAnswer')
        
        # 处理分数答案
        if problem_data.get('hasFraction') and problem_data.get('fractionAnswer'):
            fraction_answer = problem_data.get('fractionAnswer')
            if (fraction_answer.get('whole') is not None or 
                fraction_answer.get('numerator') is not None or 
                fraction_answer.get('denominator') is not None):
                # 计算分数的小数值
                whole = fraction_answer.get('whole', 0) or 0
                numerator = fraction_answer.get('numerator', 0) or 0
                denominator = fraction_answer.get('denominator', 1) or 1
                if denominator != 0:
                    user_answer = whole + numerator / denominator
        
        is_correct = False
        if user_answer is not None and correct_answer is not None:
            # 对于小数比较，允许小的误差
            is_correct = abs(float(user_answer) - float(correct_answer)) < 0.01
        
        # 计算得分: 正确为1分，错误或未答为0分
        score = 1 if is_correct else 0
        
        if is_correct:
            total_correct += 1
            total_score += score

        # 创建计算题目记录
        problem = CalculationProblem(
            user_id=batch_data.user_id,
            test_session_id=test_session_id,
            problem_index=problem_data.get('problemIndex'),
            problem_text=problem_data.get('problemText'),
            correct_answer=correct_answer,
            user_answer=user_answer if user_answer is not None else 0,
            is_correct=is_correct,
            response_time=0,  # 批量提交时没有单独的响应时间
            score=score,
        )

        session.add(problem)
        saved_problems.append(problem)

    # 更新测试会话进度和正确数量
    test_session.progress = len(batch_data.problems)
    test_session.correct_count = total_correct
    test_session.total_score = total_score

    session.add(test_session)
    session.commit()

    # 刷新所有问题对象
    for problem in saved_problems:
        session.refresh(problem)

    logger.info(f"批量保存了 {len(saved_problems)} 道题目，正确 {total_correct} 道")
    return saved_problems


def analyze_fraction_errors(fraction_problems: List[CalculationProblem]) -> Dict[str, int]:
    """分析分数运算错误类型"""
    error_types = {
        "common_denominator_error": 0,  # 通分错误
        "simplification_error": 0,      # 化简错误
        "mixed_number_error": 0,        # 带分数转换错误
        "calculation_error": 0,         # 基本计算错误
        "other_error": 0                # 其他错误
    }
    
    for problem in fraction_problems:
        if not problem.is_correct and problem.user_answer is not None:
            # 简单的错误分类逻辑
            error_diff = abs(float(problem.user_answer) - float(problem.correct_answer))
            if error_diff > 1.0:
                error_types["calculation_error"] += 1
            elif 0.1 < error_diff <= 1.0:
                error_types["common_denominator_error"] += 1
            elif 0.01 < error_diff <= 0.1:
                error_types["simplification_error"] += 1
            else:
                error_types["other_error"] += 1
    
    return error_types


def analyze_error_patterns(error_problems: List[CalculationProblem]) -> Dict[str, int]:
    """分析错误模式"""
    error_patterns = {
        "addition_errors": sum(1 for p in error_problems if "+" in p.problem_text),
        "subtraction_errors": sum(1 for p in error_problems if "-" in p.problem_text and "+" not in p.problem_text),
        "multiplication_errors": sum(1 for p in error_problems if "×" in p.problem_text),
        "fraction_errors": sum(1 for p in error_problems if "/" in p.problem_text),
        "large_number_errors": sum(1 for p in error_problems if any(char.isdigit() and int(char) > 5 for char in p.problem_text.replace(" ", "")))
    }
    
    return error_patterns


def get_common_mistakes(error_problems: List[CalculationProblem]) -> List[Dict[str, Any]]:
    """获取常见错误示例"""
    mistakes = []
    
    for problem in error_problems[:5]:  # 只返回前5个错误作为示例
        mistake = {
            "question": problem.problem_text,
            "correct_answer": problem.correct_answer,
            "user_answer": problem.user_answer,
            "error_magnitude": abs(float(problem.user_answer) - float(problem.correct_answer)) if problem.user_answer else 0
        }
        mistakes.append(mistake)
    
    return mistakes


def calculate_consistency_score(response_times: List[float]) -> float:
    """计算答题一致性分数（越高越一致）"""
    if len(response_times) < 2:
        return 100.0
    
    import statistics
    mean_time = statistics.mean(response_times)
    std_dev = statistics.stdev(response_times)
    
    # 使用变异系数计算一致性，值越小越一致
    if mean_time > 0:
        cv = std_dev / mean_time
        # 转换为百分制分数，100表示完全一致
        consistency_score = max(0, 100 - cv * 100)
        return round(consistency_score, 1)
    
    return 100.0


def get_grade_performance_analysis(session: Session, user_id: int, grade_level: int) -> Dict[str, Any]:
    """获取用户在特定年级的所有测试表现分析"""
    # 获取用户在该年级的所有测试会话
    query = select(CalculationTestSession).where(
        CalculationTestSession.user_id == user_id,
        CalculationTestSession.grade_level == grade_level,
        CalculationTestSession.is_completed == True
    ).order_by(CalculationTestSession.start_time)
    
    sessions = list(session.exec(query).all())
    
    if not sessions:
        return {"message": "没有找到已完成的测试记录"}
    
    # 计算趋势分析
    scores = [s.total_score for s in sessions]
    accuracies = [s.accuracy for s in sessions]
    times = [s.total_time_seconds for s in sessions if s.total_time_seconds]
    
    analysis = {
        "totalAttempts": len(sessions),
        "latestScore": scores[-1] if scores else 0,
        "bestScore": max(scores) if scores else 0,
        "averageScore": sum(scores) / len(scores) if scores else 0,
        "scoreImprovement": scores[-1] - scores[0] if len(scores) > 1 else 0,
        "latestAccuracy": accuracies[-1] if accuracies else 0,
        "bestAccuracy": max(accuracies) if accuracies else 0,
        "averageAccuracy": sum(accuracies) / len(accuracies) if accuracies else 0,
        "averageTime": sum(times) / len(times) if times else 0,
        "progressTrend": "improving" if len(scores) > 1 and scores[-1] > scores[0] else "stable",
        "sessions": [
            {
                "sessionId": s.id,
                "date": s.start_time.strftime("%Y-%m-%d %H:%M"),
                "score": s.total_score,
                "accuracy": s.accuracy,
                "timeSeconds": s.total_time_seconds
            } for s in sessions
        ]
    }
    
    return analysis