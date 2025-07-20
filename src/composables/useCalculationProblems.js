export function useCalculationProblems() {
  
  const generateProblems = async (gradeLevel) => {
    try {
      // 使用API获取固定题目
      const response = await fetch(`/api/calculation/grades/${gradeLevel}/problems`)
      
      if (!response.ok) {
        console.error('获取题目失败:', await response.text())
        return []
      }
      
      const fixedProblems = await response.json()
      
      // 转换为前端格式
      const problems = fixedProblems.map((problem, index) => ({
        index: index + 1,
        text: problem.problem,
        answer: problem.answer,
        type: problem.type,
        hasFraction: ['分数', 'fraction'].some(keyword => problem.type.includes(keyword))
      }))
      
      console.log(`已加载年级 ${gradeLevel} 的 ${problems.length} 道固定题目`)
      return problems
      
    } catch (error) {
      console.error('获取题目失败:', error)
      return []
    }
  }


  return {
    generateProblems
  }
}