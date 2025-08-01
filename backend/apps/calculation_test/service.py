from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlmodel import Session, select
import statistics
import re
import json
import os
from fractions import Fraction

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


def format_user_answer(problem_data: Dict[str, Any]) -> str:
    """格式化用户答案为标准格式"""
    user_answer = problem_data.get('userAnswer')
    
    # 如果用户没有回答，直接返回None
    if user_answer is None:
        return None
    
    # 处理分数答案
    if problem_data.get('hasFraction') and problem_data.get('fractionAnswer'):
        fraction_answer = problem_data.get('fractionAnswer')
        whole = fraction_answer.get('whole', 0) or 0
        numerator = fraction_answer.get('numerator', 0) or 0 
        denominator = fraction_answer.get('denominator', 1) or 1
        
        # 格式化为 a+b/c 格式
        if whole == 0 and numerator == 0:
            return "0"
        elif whole == 0:
            return f"{numerator}/{denominator}"
        elif numerator == 0:
            return str(whole)
        else:
            return f"{whole}+{numerator}/{denominator}"
    
    # 普通数字答案
    return str(user_answer)


def parse_answer(answer_str: str) -> float:
    """解析答案字符串为数值"""
    if not answer_str or answer_str == "0":
        return 0.0
    
    # 处理循环小数格式，如 "8.1[3]" 或 "0.8[54]"
    if '[' in answer_str and ']' in answer_str:
        # 暂时移除循环节，只取非循环部分进行数值比较
        # 这里简化处理，实际应用中可能需要更精确的循环小数转换
        base_part = answer_str.split('[')[0]
        try:
            return float(base_part)
        except ValueError:
            return 0.0
    
    # 处理带分数格式 a+b/c
    if '+' in answer_str and '/' in answer_str:
        parts = answer_str.split('+')
        if len(parts) == 2:
            whole = float(parts[0])
            fraction_part = parts[1]
            if '/' in fraction_part:
                num, den = fraction_part.split('/')
                return whole + float(num) / float(den)
    
    # 处理纯分数格式 b/c
    elif '/' in answer_str:
        num, den = answer_str.split('/')
        return float(num) / float(den)
    
    # 处理普通数字
    try:
        return float(answer_str)
    except ValueError:
        return 0.0


def compare_answers(user_answer_str: str, correct_answer_str: str) -> bool:
    """比较用户答案和正确答案"""
    if not user_answer_str or not correct_answer_str:
        return False
    
    try:
        # 首先尝试字符串直接比较（适用于循环小数格式）
        user_str = str(user_answer_str).strip()
        correct_str = str(correct_answer_str).strip()
        
        if user_str == correct_str:
            return True
        
        # 如果字符串不匹配，尝试数值比较
        user_value = parse_answer(user_str)
        correct_value = parse_answer(correct_str)
        
        # 允许小的数值误差
        return abs(user_value - correct_value) < 0.01
    except Exception:
        return False


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
    try:
        # 检查会话是否存在
        test_session = session.get(CalculationTestSession, test_session_id)
        if not test_session:
            logger.error(f"测试会话不存在: ID={test_session_id}")
            raise ValueError(f"测试会话不存在: ID={test_session_id}")

        # 检查用户是否存在
        user = session.get(User, problem_data.user_id)
        if not user:
            logger.error(f"用户不存在: ID={problem_data.user_id}")
            raise ValueError(f"用户不存在: ID={problem_data.user_id}")

        # 验证用户答案是否正确
        is_correct = compare_answers(problem_data.user_answer, problem_data.correct_answer)
        
        # 计算得分: 正确为1分，错误或未答为0分
        score = 1 if is_correct else 0

        # 创建计算题目记录
        problem = CalculationProblem(
            user_id=problem_data.user_id,
            test_session_id=test_session_id,
            problem_index=problem_data.problem_index,
            problem_text=problem_data.problem_text,
            problem_type=getattr(problem_data, 'problem_type', None),
            correct_answer=str(problem_data.correct_answer),
            user_answer=str(problem_data.user_answer) if problem_data.user_answer is not None else None,
            is_correct=is_correct,
            response_time=problem_data.response_time,
            score=score,
        )
    except Exception as e:
        logger.error(f"保存题目失败: {str(e)}", exc_info=True)
        raise

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
    try:
        # 获取测试会话
        test_session = session.get(CalculationTestSession, test_session_id)
        if not test_session:
            logger.error(f"测试会话不存在: ID={test_session_id}")
            return None

        # 获取用户
        user = session.get(User, test_session.user_id) if test_session.user_id else None

        # 获取所有计算题目记录
        problems = get_session_problems(session, test_session_id)
    except Exception as e:
        logger.error(f"获取测试会话结果失败: {str(e)}", exc_info=True)
        raise

    # 初始化统计数据
    valid_response_times = [p.response_time for p in problems if p.response_time and p.response_time > 0]
    total_response_time = sum(valid_response_times)
    avg_response_time = total_response_time / max(len(valid_response_times), 1) if valid_response_times else 0
    
    # 计算平均响应时间（转换为秒）
    avg_response_time_seconds = avg_response_time / 1000 if avg_response_time > 0 else 0
    
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
        "averageResponseTime": avg_response_time_seconds,
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
        # 四年级: 使用题目类型进行统计
        two_digit_add_sub = [p for p in problems if p.problem_type == "twoDigitAddSub"]
        two_digit_mult = [p for p in problems if p.problem_type == "twoDigitMult"]
        fraction_add_sub = [p for p in problems if p.problem_type == "fractionAddSub"]
        three_digit_mult = [p for p in problems if p.problem_type == "threeDigitMult"]
        
        # 计算每种题型的平均时间（转换为秒）
        def calc_avg_time(problem_list):
            valid_times = [p.response_time for p in problem_list if p.response_time and p.response_time > 0]
            return (sum(valid_times) / len(valid_times) / 1000) if valid_times else 0
        
        stats["problemTypeStats"] = {
            "twoDigitAddSub": {
                "total": len(two_digit_add_sub),
                "completed": sum(1 for p in two_digit_add_sub if p.user_answer is not None),
                "correct": sum(1 for p in two_digit_add_sub if p.is_correct),
                "accuracy": sum(1 for p in two_digit_add_sub if p.is_correct) / max(len(two_digit_add_sub), 1) * 100,
                "avgResponseTime": calc_avg_time(two_digit_add_sub),
                "errors": [p for p in two_digit_add_sub if not p.is_correct and p.user_answer is not None]
            },
            "twoDigitMult": {
                "total": len(two_digit_mult),
                "completed": sum(1 for p in two_digit_mult if p.user_answer is not None),
                "correct": sum(1 for p in two_digit_mult if p.is_correct),
                "accuracy": sum(1 for p in two_digit_mult if p.is_correct) / max(len(two_digit_mult), 1) * 100,
                "avgResponseTime": calc_avg_time(two_digit_mult),
                "errors": [p for p in two_digit_mult if not p.is_correct and p.user_answer is not None]
            },
            "fractionAddSub": {
                "total": len(fraction_add_sub),
                "completed": sum(1 for p in fraction_add_sub if p.user_answer is not None),
                "correct": sum(1 for p in fraction_add_sub if p.is_correct),
                "accuracy": sum(1 for p in fraction_add_sub if p.is_correct) / max(len(fraction_add_sub), 1) * 100,
                "avgResponseTime": calc_avg_time(fraction_add_sub),
                "errors": [p for p in fraction_add_sub if not p.is_correct and p.user_answer is not None]
            },
            "threeDigitMult": {
                "total": len(three_digit_mult),
                "completed": sum(1 for p in three_digit_mult if p.user_answer is not None),
                "correct": sum(1 for p in three_digit_mult if p.is_correct),
                "accuracy": sum(1 for p in three_digit_mult if p.is_correct) / max(len(three_digit_mult), 1) * 100,
                "avgResponseTime": calc_avg_time(three_digit_mult),
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
            mult_valid_times = [p.response_time for p in mult_problems if p.response_time and p.response_time > 0]
            mult_avg_time = (sum(mult_valid_times) / len(mult_valid_times) / 1000) if mult_valid_times else 0
            stats["multiplicationAnalysis"] = {
                "total": len(mult_problems),
                "correct": sum(1 for p in mult_problems if p.is_correct),
                "accuracy": sum(1 for p in mult_problems if p.is_correct) / len(mult_problems) * 100,
                "avgResponseTime": mult_avg_time
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
        
        # 计算各段的平均响应时间（转换为秒）
        def calc_avg_section_time(section):
            valid_times = [p.response_time for p in section if p.response_time and p.response_time > 0]
            return (sum(valid_times) / len(valid_times) / 1000) if valid_times else 0
        
        stats["difficultyAnalysis"] = {
            "firstThird": {
                "accuracy": sum(1 for p in first_third if p.is_correct) / max(len(first_third), 1) * 100,
                "avgResponseTime": calc_avg_section_time(first_third)
            },
            "secondThird": {
                "accuracy": sum(1 for p in second_third if p.is_correct) / max(len(second_third), 1) * 100,
                "avgResponseTime": calc_avg_section_time(second_third)
            },
            "lastThird": {
                "accuracy": sum(1 for p in last_third if p.is_correct) / max(len(last_third), 1) * 100,
                "avgResponseTime": calc_avg_section_time(last_third)
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
        
        # 速度分析（转换为秒）
        response_times = [p.response_time for p in problems if p.response_time and p.response_time > 0]
        if response_times:
            response_times_seconds = [t / 1000 for t in response_times]  # 转换为秒
            stats["speedAnalysis"] = {
                "fastest": min(response_times_seconds),
                "slowest": max(response_times_seconds),
                "median": sorted(response_times_seconds)[len(response_times_seconds)//2],
                "consistencyScore": calculate_consistency_score(response_times_seconds)
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
    try:
        # 检查会话是否存在
        test_session = session.get(CalculationTestSession, test_session_id)
        if not test_session:
            logger.error(f"测试会话不存在: ID={test_session_id}")
            raise ValueError(f"测试会话不存在: ID={test_session_id}")

        # 检查用户是否存在
        user = session.get(User, batch_data.user_id)
        if not user:
            logger.error(f"用户不存在: ID={batch_data.user_id}")
            raise ValueError(f"用户不存在: ID={batch_data.user_id}")
    except Exception as e:
        logger.error(f"批量保存题目前置检查失败: {str(e)}", exc_info=True)
        raise

    saved_problems = []
    total_correct = 0
    total_score = 0

    # 处理每个题目
    for problem_data in batch_data.problems:
        # 格式化答案
        formatted_user_answer = format_user_answer(problem_data)
        correct_answer = problem_data.get('correctAnswer')
        
        # 验证用户答案是否正确
        is_correct = False
        if formatted_user_answer is not None and correct_answer is not None:
            is_correct = compare_answers(formatted_user_answer, str(correct_answer))
        
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
            problem_type=problem_data.get('type'),
            correct_answer=str(correct_answer),
            user_answer=formatted_user_answer,
            is_correct=is_correct,
            response_time=problem_data.get('responseTime', 0),  # 支持从前端传入响应时间
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
            try:
                # 使用 parse_answer 函数解析带分数格式
                user_value = parse_answer(problem.user_answer)
                correct_value = parse_answer(problem.correct_answer)
                error_diff = abs(user_value - correct_value)
                
                if error_diff > 1.0:
                    error_types["calculation_error"] += 1
                elif 0.1 < error_diff <= 1.0:
                    error_types["common_denominator_error"] += 1
                elif 0.01 < error_diff <= 0.1:
                    error_types["simplification_error"] += 1
                else:
                    error_types["other_error"] += 1
            except Exception:
                # 解析失败时归类为其他错误
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
        try:
            user_value = parse_answer(problem.user_answer) if problem.user_answer else 0
            correct_value = parse_answer(problem.correct_answer) if problem.correct_answer else 0
            error_magnitude = abs(user_value - correct_value)
        except:
            error_magnitude = 0
            
        mistake = {
            "question": problem.problem_text,
            "correct_answer": problem.correct_answer,
            "user_answer": problem.user_answer,
            "error_magnitude": error_magnitude
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


def get_fixed_problems_for_grade(grade_level: int) -> List[Dict[str, Any]]:
    """获取指定年级的固定题目"""
    try:
        # 构建文件路径
        if grade_level >= 7:
            filename = f"grade-7+-answers.json"
        else:
            filename = f"grade-{grade_level}-answers.json"
        
        # 获取文件绝对路径（相对于项目根目录）
        # 当前文件: backend/apps/calculation_test/service.py
        # 目标路径: src/components/calculation/
        current_file = os.path.abspath(__file__)
        # 向上三级到 backend/ 目录
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        # 再向上一级到项目根目录
        project_root = os.path.dirname(backend_dir)
        file_path = os.path.join(project_root, "src", "components", "calculation", filename)
        
        # 读取JSON文件
        if not os.path.exists(file_path):
            logger.error(f"题目文件不存在: {file_path}")
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            problems = json.load(f)
        
        logger.info(f"成功加载年级 {grade_level} 的 {len(problems)} 道题目")
        return problems
        
    except Exception as e:
        logger.error(f"读取年级 {grade_level} 题目失败: {str(e)}", exc_info=True)
        return []