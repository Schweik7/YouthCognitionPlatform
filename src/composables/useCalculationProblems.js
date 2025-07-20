export function useCalculationProblems() {
  
  const generateProblems = async (gradeLevel) => {
    try {
      // 使用新的API获取固定题目
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

  // 分数运算辅助函数
  const gcd = (a, b) => {
    while (b !== 0) {
      const temp = b
      b = a % b
      a = temp
    }
    return a
  }

  const lcm = (a, b) => {
    return (a * b) / gcd(a, b)
  }

  const simplifyFraction = (numerator, denominator) => {
    if (numerator === 0) return { numerator: 0, denominator: 1 }
    const divisor = gcd(Math.abs(numerator), Math.abs(denominator))
    return {
      numerator: numerator / divisor,
      denominator: denominator / divisor
    }
  }

  const toMixedNumber = (numerator, denominator) => {
    if (numerator === 0) {
      return { whole: 0, numerator: 0, denominator: 1 }
    }
    const whole = Math.floor(numerator / denominator)
    const remainder = numerator % denominator
    return {
      whole: whole,
      numerator: remainder,
      denominator: denominator
    }
  }

  const addFractions = (n1, d1, n2, d2) => {
    const commonDenominator = lcm(d1, d2)
    const newN1 = n1 * (commonDenominator / d1)
    const newN2 = n2 * (commonDenominator / d2)
    return {
      numerator: newN1 + newN2,
      denominator: commonDenominator
    }
  }

  const subtractFractions = (n1, d1, n2, d2) => {
    const commonDenominator = lcm(d1, d2)
    const newN1 = n1 * (commonDenominator / d1)
    const newN2 = n2 * (commonDenominator / d2)
    return {
      numerator: newN1 - newN2,
      denominator: commonDenominator
    }
  }

  const generateFractionAddSub = () => {
    // 生成两个不同分母的分数相加减，需要通分
    const denominator1 = Math.floor(Math.random() * 6) + 2  // 2-7
    let denominator2 = Math.floor(Math.random() * 6) + 2  // 2-7
    
    // 确保分母不同，增加通分的复杂性
    while (denominator1 === denominator2) {
      denominator2 = Math.floor(Math.random() * 6) + 2
    }
    
    const isAddition = Math.random() < 0.5
    let numerator1, numerator2
    
    if (isAddition) {
      // 加法时避免分子和分母相同（避免1这样的整数）
      numerator1 = Math.floor(Math.random() * (denominator1 - 1)) + 1  // 1 到 denominator1-1
      numerator2 = Math.floor(Math.random() * (denominator2 - 1)) + 1  // 1 到 denominator2-1
    } else {
      // 减法时可以允许分子和分母相同
      numerator1 = Math.floor(Math.random() * denominator1) + 1  // 1 到 denominator1
      numerator2 = Math.floor(Math.random() * denominator2) + 1  // 1 到 denominator2
    }
    let result
    
    if (isAddition) {
      result = addFractions(numerator1, denominator1, numerator2, denominator2)
    } else {
      // 确保结果不为负数
      const frac1Value = numerator1 / denominator1
      const frac2Value = numerator2 / denominator2
      
      if (frac1Value >= frac2Value) {
        result = subtractFractions(numerator1, denominator1, numerator2, denominator2)
      } else {
        result = subtractFractions(numerator2, denominator2, numerator1, denominator1)
        // 交换分数顺序，确保结果为正
        const simplified = simplifyFraction(result.numerator, result.denominator)
        const mixed = toMixedNumber(simplified.numerator, simplified.denominator)
        return {
          text: `${numerator2}/${denominator2} - ${numerator1}/${denominator1} = `,
          answer: calculateFinalAnswer(result.numerator, result.denominator),
          fractionAnswer: mixed,
          stringAnswer: formatFractionAnswer(mixed.whole, mixed.numerator, mixed.denominator)
        }
      }
    }
    
    // 化简分数
    const simplified = simplifyFraction(result.numerator, result.denominator)
    const mixed = toMixedNumber(simplified.numerator, simplified.denominator)
    
    return {
      text: `${numerator1}/${denominator1} ${isAddition ? '+' : '-'} ${numerator2}/${denominator2} = `,
      answer: calculateFinalAnswer(result.numerator, result.denominator),
      fractionAnswer: mixed,
      stringAnswer: formatFractionAnswer(mixed.whole, mixed.numerator, mixed.denominator)
    }
  }
  
  const calculateFinalAnswer = (numerator, denominator) => {
    if (numerator === 0) return 0
    const simplified = simplifyFraction(numerator, denominator)
    const mixed = toMixedNumber(simplified.numerator, simplified.denominator)
    
    // 如果分子为0，返回整数部分
    if (mixed.numerator === 0) {
      return mixed.whole
    }
    
    return mixed.whole + (mixed.numerator / mixed.denominator)
  }
  
  const convertToMixedNumber = (numerator, denominator) => {
    if (numerator === 0) {
      return { whole: 0, numerator: 0, denominator: 1 }
    }
    const simplified = simplifyFraction(numerator, denominator)
    const mixed = toMixedNumber(simplified.numerator, simplified.denominator)
    
    // 如果化简后分子为0，返回纯整数
    if (mixed.numerator === 0) {
      return { whole: mixed.whole, numerator: 0, denominator: 1 }
    }
    
    return mixed
  }

  const formatFractionAnswer = (whole, numerator, denominator) => {
    /**
     * 将分数格式化为标准字符串：a+b/c
     */
    if (whole === 0 && numerator === 0) {
      return "0"
    } else if (whole === 0) {
      return `${numerator}/${denominator}`
    } else if (numerator === 0) {
      return `${whole}`
    } else {
      return `${whole}+${numerator}/${denominator}`
    }
  }

  const generateFractionIntegerAddSub = () => {
    // 生成分数与整数相加减
    const denominator = Math.floor(Math.random() * 6) + 2  // 2-7
    const numerator = Math.floor(Math.random() * denominator) + 1  // 1 到 denominator
    const integer = Math.floor(Math.random() * 4) + 1  // 1-4
    
    const isAddition = Math.random() < 0.5
    let result
    let operationText
    
    if (isAddition) {
      // 分数 + 整数：n/d + i = (n + i*d)/d
      result = {
        numerator: numerator + integer * denominator,
        denominator: denominator
      }
      operationText = `${numerator}/${denominator} + ${integer} = `
    } else {
      // 确保结果不为负数
      const fractionValue = numerator / denominator
      if (integer > fractionValue) {
        // 整数 - 分数：i - n/d = (i*d - n)/d
        result = {
          numerator: integer * denominator - numerator,
          denominator: denominator
        }
        operationText = `${integer} - ${numerator}/${denominator} = `
      } else {
        // 分数 - 整数：n/d - i = (n - i*d)/d
        // 如果结果为负，改为加法
        if (numerator < integer * denominator) {
          result = {
            numerator: numerator + integer * denominator,
            denominator: denominator
          }
          operationText = `${numerator}/${denominator} + ${integer} = `
        } else {
          result = {
            numerator: numerator - integer * denominator,
            denominator: denominator
          }
          operationText = `${numerator}/${denominator} - ${integer} = `
        }
      }
    }
    
    // 化简分数
    const simplified = simplifyFraction(result.numerator, result.denominator)
    const mixed = toMixedNumber(simplified.numerator, simplified.denominator)
    
    return {
      text: operationText,
      answer: calculateFinalAnswer(result.numerator, result.denominator),
      fractionAnswer: mixed,
      stringAnswer: formatFractionAnswer(mixed.whole, mixed.numerator, mixed.denominator)
    }
  }

  const generateGrade1Problems = (problems) => {
    // 加法题：20道
    for (let i = 0; i < 20; i++) {
      let a, b
      if (Math.random() < 0.3) {
        a = 10
        b = Math.floor(Math.random() * 10)
      } else {
        a = Math.floor(Math.random() * 10) + 1
        b = Math.floor(Math.random() * (11 - a))
      }

      problems.push({
        index: i + 1,
        text: `${a} + ${b} = `,
        answer: a + b,
        type: "addition",
        hasFraction: false
      })
    }

    // 减法题：20道
    for (let i = 0; i < 20; i++) {
      let a, b
      if (Math.random() < 0.3) {
        a = 10
        b = Math.floor(Math.random() * 11)
      } else {
        a = Math.floor(Math.random() * 10) + 1
        b = Math.floor(Math.random() * (a + 1))
      }

      problems.push({
        index: i + 21,
        text: `${a} - ${b} = `,
        answer: a - b,
        type: "subtraction",
        hasFraction: false
      })
    }
  }

  const generateGrade2Problems = (problems) => {
    // 第一部分：30道两数加减法
    for (let i = 0; i < 30; i++) {
      let a, b, isAddition = Math.random() < 0.5

      if (isAddition) {
        a = Math.floor(Math.random() * 90) + 10
        b = Math.floor(Math.random() * (101 - a))
        problems.push({
          index: i + 1,
          text: `${a} + ${b} = `,
          answer: a + b,
          type: "twoNumbers",
          hasFraction: false
        })
      } else {
        a = Math.floor(Math.random() * 90) + 10  // 10-99
        b = Math.floor(Math.random() * a) + 1    // 1-a，确保 a >= b
        problems.push({
          index: i + 1,
          text: `${a} - ${b} = `,
          answer: a - b,
          type: "twoNumbers",
          hasFraction: false
        })
      }
    }

    // 第二部分：10道三数加减法
    for (let i = 0; i < 10; i++) {
      const {text, answer} = generateThreeNumberExpression(50, 100)
      problems.push({
        index: i + 31,
        text: text,
        answer: answer,
        type: "threeNumbers",
        hasFraction: false
      })
    }
  }

  const generateGrade3Problems = (problems) => {
    // 第一部分：10道三位数和两位数的加减法
    for (let i = 0; i < 10; i++) {
      let a, b, isAddition = Math.random() < 0.5

      if (isAddition) {
        a = Math.floor(Math.random() * 900) + 100
        b = Math.floor(Math.random() * 90) + 10
        problems.push({
          index: i + 1,
          text: `${a} + ${b} = `,
          answer: a + b,
          type: "type1",
          hasFraction: false
        })
      } else {
        a = Math.floor(Math.random() * 900) + 100  // 100-999
        b = Math.floor(Math.random() * 90) + 10   // 10-99
        // 确保 a > b，如果不满足则调整
        if (a <= b) {
          a = b + Math.floor(Math.random() * 100) + 1
        }
        problems.push({
          index: i + 1,
          text: `${a} - ${b} = `,
          answer: a - b,
          type: "type1",
          hasFraction: false
        })
      }
    }

    // 第二部分：20道三位数与三位数的加减法
    for (let i = 0; i < 20; i++) {
      let a, b, isAddition = Math.random() < 0.5

      if (isAddition) {
        a = Math.floor(Math.random() * 500) + 100
        b = Math.floor(Math.random() * (1000 - a - 100)) + 100
        problems.push({
          index: i + 11,
          text: `${a} + ${b} = `,
          answer: a + b,
          type: "type2",
          hasFraction: false
        })
      } else {
        a = Math.floor(Math.random() * 900) + 100
        b = Math.floor(Math.random() * (a - 100)) + 100
        problems.push({
          index: i + 11,
          text: `${a} - ${b} = `,
          answer: a - b,
          type: "type2",
          hasFraction: false
        })
      }
    }

    // 第三部分：10道三位数3个数字的加减法
    for (let i = 0; i < 10; i++) {
      const {text, answer} = generateThreeNumberExpression(100, 500, true)
      problems.push({
        index: i + 31,
        text: text,
        answer: answer,
        type: "type3",
        hasFraction: false
      })
    }
  }

  const generateGrade4Problems = (problems) => {
    // 第一部分：10道两位数加减法
    for (let i = 0; i < 10; i++) {
      let a, b, isAddition = Math.random() < 0.5
      
      if (isAddition) {
        a = Math.floor(Math.random() * 90) + 10  // 10-99
        b = Math.floor(Math.random() * 90) + 10  // 10-99
        // 确保结果不为负数
        problems.push({
          index: i + 1,
          text: `${a} + ${b} = `,
          answer: a + b,
          type: "twoDigitAddSub",
          hasFraction: false
        })
      } else {
        a = Math.floor(Math.random() * 90) + 10  // 10-99
        b = Math.floor(Math.random() * a) + 1    // 1 到 a，确保结果不为负数
        problems.push({
          index: i + 1,
          text: `${a} - ${b} = `,
          answer: a - b,
          type: "twoDigitAddSub",
          hasFraction: false
        })
      }
    }

    // 第二部分：10道两位数乘法
    for (let i = 0; i < 10; i++) {
      let a = Math.floor(Math.random() * 90) + 10  // 10-99
      let b = Math.floor(Math.random() * 90) + 10  // 10-99
      
      problems.push({
        index: i + 11,
        text: `${a} × ${b} = `,
        answer: a * b,
        type: "twoDigitMult",
        hasFraction: false
      })
    }

    // 第三部分：10道分数加减法（全部为分数+分数，避免整数+分数的简单情况）
    for (let i = 0; i < 10; i++) {
      // 只生成两个分数相加减
      let fractionProblem = generateFractionAddSub()
      
      problems.push({
        index: i + 21,
        text: fractionProblem.text,
        answer: fractionProblem.stringAnswer || fractionProblem.answer, // 优先使用字符串格式
        type: "fractionAddSub",
        hasFraction: true,
        fractionAnswer: fractionProblem.fractionAnswer
      })
    }

    // 第四部分：10道三位数乘两位数
    for (let i = 0; i < 10; i++) {
      let a = Math.floor(Math.random() * 900) + 100  // 100-999
      let b = Math.floor(Math.random() * 90) + 10    // 10-99
      
      problems.push({
        index: i + 31,
        text: `${a} × ${b} = `,
        answer: a * b,
        type: "threeDigitMult",
        hasFraction: false
      })
    }
  }

  const generateGrade5Problems = (problems) => {
    // 五年级小数运算 - 40道题目
    const fixedProblems = [
      {text: "5 × 2.42 = ", answer: 12.1, type: "decimal"},
      {text: "(254 + 8) × 47 = ", answer: 12314, type: "decimal"},
      {text: "12.2 ÷ 2 = ", answer: 6.1, type: "decimal"},
      {text: "156 × 7 × 4 = ", answer: 4368, type: "decimal"},
      {text: "14.5 ÷ 4 = ", answer: 3.625, type: "decimal"},
      {text: "45 ÷ 5 ÷ 3 = ", answer: 3, type: "decimal"},
      {text: "3 × 1.56 = ", answer: 4.68, type: "decimal"},
      {text: "0.6 × 7.8 = ", answer: 4.68, type: "decimal"},
      {text: "43 × 8 + 36 ÷ 6 = ", answer: 350, type: "decimal"},
      {text: "24.4 ÷ 3 = ", answer: 8.13, type: "decimal", hasRepeating: true},
      {text: "700 - [6 × (18 + 45)] = ", answer: 322, type: "decimal"},
      {text: "1.3 × 5.6 = ", answer: 7.28, type: "decimal"},
      {text: "0.05 ÷ 10 = ", answer: 0.005, type: "decimal"},
      {text: "9.4 ÷ 11 = ", answer: 0.85, type: "decimal", hasRepeating: true},
      {text: "41.6 ÷ 40 = ", answer: 1.04, type: "decimal"},
      {text: "35.1 ÷ 30 = ", answer: 1.17, type: "decimal"},
      {text: "0.06 ÷ 12 = ", answer: 0.005, type: "decimal"},
      {text: "18.9 × 0.04 = ", answer: 0.756, type: "decimal"},
      {text: "26.3 × 1.07 = ", answer: 28.141, type: "decimal"},
      {text: "2.5 × 13 + 0.9 = ", answer: 33.4, type: "decimal"},
      {text: "2.6 × 2.14 = ", answer: 5.564, type: "decimal"},
      {text: "76.14 ÷ 0.27 = ", answer: 282, type: "decimal"},
      {text: "49.84 ÷ 0.56 = ", answer: 89, type: "decimal"},
      {text: "8.1 ÷ 1.85 = ", answer: 4.38, type: "decimal", hasRepeating: true},
      {text: "20.88 ÷ 3.48 = ", answer: 6, type: "decimal"},
      {text: "73 ÷ 3 = ", answer: 24.33, type: "decimal", hasRepeating: true},
      {text: "25 ÷ 6 = ", answer: 4.17, type: "decimal", hasRepeating: true},
      {text: "3.7 × 5.47 = ", answer: 20.239, type: "decimal"},
      {text: "35 ÷ 11 = ", answer: 3.18, type: "decimal", hasRepeating: true},
      {text: "200 ÷ 20.32 = ", answer: 9.84, type: "decimal"},
      {text: "300 ÷ 18.65 = ", answer: 16.09, type: "decimal"},
      {text: "35 × 8.1 + 1.7 = ", answer: 285.2, type: "decimal"},
      {text: "76.6 - 6.6 × 3 = ", answer: 56.8, type: "decimal"},
      {text: "59.8 - 4.2 × 5 = ", answer: 38.8, type: "decimal"},
      {text: "0.79 × 4.8 + 0.79 × 5.2 = ", answer: 7.9, type: "decimal"},
      {text: "8.02 × 5.3 + 4.52 × 4.7 = ", answer: 63.75, type: "decimal"},
      {text: "(8 + 0.8) × 1.25 = ", answer: 11, type: "decimal"},
      {text: "(5 + 3.9) × 5.68 = ", answer: 50.552, type: "decimal"},
      {text: "2.5 × 0.6 - 1.8 × 0.5 = ", answer: 0.6, type: "decimal"},
      {text: "7.1 × 1.5 - 5.4 × 0.3 = ", answer: 9.03, type: "decimal"}
    ]

    // 添加固定题目
    fixedProblems.forEach((problem, index) => {
      problems.push({
        index: index + 1,
        text: problem.text,
        answer: problem.answer,
        type: problem.type,
        hasFraction: false,
        hasRepeating: problem.hasRepeating || false
      })
    })
  }

  const generateGrade6Problems = (problems) => {
    // 第一部分：15道基础乘法（类似三年级的type1）
    for (let i = 0; i < 15; i++) {
      let a, b
      if (Math.random() < 0.3) {
        // 类似三年级的三位数+两位数模式：大数乘小数
        a = Math.floor(Math.random() * 9) + 1
        b = Math.floor(Math.random() * 9) + 1
      } else {
        // 两位数乘法
        a = Math.floor(Math.random() * 9) + 1
        b = Math.floor(Math.random() * 9) + 1
      }

      problems.push({
        index: i + 1,
        text: `${a} × ${b} = `,
        answer: a * b,
        type: "multiplication",
        hasFraction: false
      })
    }

    // 第二部分：15道除法题（类似三年级的type2）
    for (let i = 0; i < 15; i++) {
      let dividend, divisor
      // 简单整除
      divisor = Math.floor(Math.random() * 9) + 1
      let quotient = Math.floor(Math.random() * 19) + 1
      dividend = divisor * quotient

      problems.push({
        index: i + 16,
        text: `${dividend} ÷ ${divisor} = `,
        answer: quotient,
        type: "division",
        hasFraction: false
      })
    }

    // 第三部分：10道复杂分数运算（类似三年级的type3）
    for (let i = 0; i < 10; i++) {
      const {text, answer, hasFraction} = generateComplexFraction()
      problems.push({
        index: i + 31,
        text: text,
        answer: answer,
        type: "mixed",
        hasFraction: hasFraction
      })
    }
  }

  const generateThreeNumberExpression = (min, max, threeDigit = false) => {
    let a, b, c, op1, op2, text, answer

    op1 = Math.random() < 0.5 ? "+" : "-"
    op2 = Math.random() < 0.5 ? "+" : "-"

    if (threeDigit) {
      a = Math.floor(Math.random() * (max - min)) + min
      b = Math.floor(Math.random() * (max - min)) + min
      c = Math.floor(Math.random() * (max - min)) + min
    } else {
      a = Math.floor(Math.random() * (max - min)) + min
      b = Math.floor(Math.random() * 40) + 1
      c = Math.floor(Math.random() * 40) + 1
    }

    if (op1 === "+") {
      let midResult = a + b
      if (op2 === "+") {
        text = `${a} + ${b} + ${c} = `
        answer = midResult + c
      } else {
        c = Math.min(c, midResult)
        text = `${a} + ${b} - ${c} = `
        answer = midResult - c
      }
    } else {
      b = Math.min(b, a)
      let midResult = a - b
      if (op2 === "+") {
        text = `${a} - ${b} + ${c} = `
        answer = midResult + c
      } else {
        c = Math.min(c, midResult)
        text = `${a} - ${b} - ${c} = `
        answer = midResult - c
      }
    }

    return { text, answer }
  }

  const generateMixedExpression = () => {
    // 简单的混合运算：加减乘除组合
    let a = Math.floor(Math.random() * 20) + 1
    let b = Math.floor(Math.random() * 10) + 1
    let c = Math.floor(Math.random() * 10) + 1
    
    if (Math.random() < 0.5) {
      // a × b + c
      return {
        text: `${a} × ${b} + ${c} = `,
        answer: a * b + c
      }
    } else {
      // a × b - c
      let product = a * b
      c = Math.min(c, product)
      return {
        text: `${a} × ${b} - ${c} = `,
        answer: product - c
      }
    }
  }

  const generateDecimalExpression = () => {
    // 小数运算
    let a = (Math.floor(Math.random() * 900) + 100) / 10 // 10.0-99.9
    let b = (Math.floor(Math.random() * 90) + 10) / 10   // 1.0-9.9
    
    if (Math.random() < 0.5) {
      return {
        text: `${a} + ${b} = `,
        answer: Math.round((a + b) * 10) / 10
      }
    } else {
      return {
        text: `${a} - ${b} = `,
        answer: Math.round((a - b) * 10) / 10
      }
    }
  }

  const generateFractionExpression = () => {
    // 简化的分数运算（转换为小数）
    let numerator1 = Math.floor(Math.random() * 8) + 1
    let denominator1 = Math.floor(Math.random() * 8) + 2
    let numerator2 = Math.floor(Math.random() * 8) + 1
    let denominator2 = denominator1 // 使用相同分母简化计算
    
    if (Math.random() < 0.5) {
      return {
        text: `${numerator1}/${denominator1} + ${numerator2}/${denominator2} = (小数)`,
        answer: Math.round((numerator1/denominator1 + numerator2/denominator2) * 100) / 100,
        hasFraction: false
      }
    } else {
      return {
        text: `${numerator1}/${denominator1} - ${numerator2}/${denominator2} = (小数)`,
        answer: Math.round((numerator1/denominator1 - numerator2/denominator2) * 100) / 100,
        hasFraction: false
      }
    }
  }

  const generateSimpleFraction = () => {
    // 四年级简单分数：1/2, 1/3, 1/4, 2/3, 3/4 等
    const fractions = [
      {text: "1/2", decimal: 0.5},
      {text: "1/3", decimal: 0.33},
      {text: "1/4", decimal: 0.25},
      {text: "2/3", decimal: 0.67},
      {text: "3/4", decimal: 0.75}
    ]
    
    const fraction = fractions[Math.floor(Math.random() * fractions.length)]
    
    return {
      text: `${fraction.text} = (带分数)`,
      answer: fraction.decimal,
      hasFraction: true
    }
  }

  const generateGradeFraction = () => {
    // 五年级分数：带分数运算
    const whole = Math.floor(Math.random() * 3) + 1  // 1-3
    const numerator = Math.floor(Math.random() * 3) + 1  // 1-3
    const denominator = Math.floor(Math.random() * 3) + 2  // 2-4
    
    const decimal = whole + numerator/denominator
    
    return {
      text: `${whole} ${numerator}/${denominator} = (带分数)`,
      answer: Math.round(decimal * 100) / 100,
      hasFraction: true
    }
  }

  const generateComplexFraction = () => {
    // 六年级复杂分数：两个带分数运算
    const whole1 = Math.floor(Math.random() * 2) + 1  // 1-2
    const numerator1 = Math.floor(Math.random() * 3) + 1  // 1-3
    const denominator1 = Math.floor(Math.random() * 3) + 2  // 2-4
    
    const whole2 = Math.floor(Math.random() * 2) + 1  // 1-2
    const numerator2 = Math.floor(Math.random() * 3) + 1  // 1-3
    const denominator2 = denominator1  // 使用相同分母
    
    const decimal1 = whole1 + numerator1/denominator1
    const decimal2 = whole2 + numerator2/denominator2
    
    const isAddition = Math.random() < 0.5
    const result = isAddition ? decimal1 + decimal2 : decimal1 - decimal2
    
    return {
      text: `${whole1} ${numerator1}/${denominator1} ${isAddition ? '+' : '-'} ${whole2} ${numerator2}/${denominator2} = (带分数)`,
      answer: Math.round(result * 100) / 100,
      hasFraction: true
    }
  }

  const generatePercentageExpression = () => {
    // 百分数运算
    let base = Math.floor(Math.random() * 90) + 10 // 10-99
    let percentage = Math.floor(Math.random() * 50) + 10 // 10%-59%
    
    return {
      text: `${base}的${percentage}% = `,
      answer: Math.round(base * percentage / 100 * 10) / 10
    }
  }

  const generateRatioExpression = () => {
    // 比例运算
    let a = Math.floor(Math.random() * 8) + 2
    let b = Math.floor(Math.random() * 8) + 2
    let c = Math.floor(Math.random() * 8) + 2
    
    return {
      text: `${a}:${b} = ${c}:? (求?)`,
      answer: Math.round(b * c / a * 10) / 10
    }
  }

  const shuffleProblems = (problems) => {
    // 分离分数题和常规题
    const fractionProblems = problems.filter(p => p.hasFraction)
    const regularProblems = problems.filter(p => !p.hasFraction)
    
    // 分别打乱
    for (let i = fractionProblems.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1))
      ;[fractionProblems[i], fractionProblems[j]] = [fractionProblems[j], fractionProblems[i]]
    }
    
    for (let i = regularProblems.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1))
      ;[regularProblems[i], regularProblems[j]] = [regularProblems[j], regularProblems[i]]
    }
    
    // 重新组合：确保分数题成对出现（每两个为一组）
    const reorganized = []
    let regIndex = 0
    let fracIndex = 0
    
    while (regIndex < regularProblems.length || fracIndex < fractionProblems.length) {
      // 添加两道常规题
      for (let i = 0; i < 2 && regIndex < regularProblems.length; i++) {
        reorganized.push(regularProblems[regIndex++])
      }
      
      // 添加两道分数题
      for (let i = 0; i < 2 && fracIndex < fractionProblems.length; i++) {
        reorganized.push(fractionProblems[fracIndex++])
      }
    }
    
    // 更新原数组
    problems.splice(0, problems.length, ...reorganized)
    
    // 重新设置题目序号
    problems.forEach((problem, index) => {
      problem.index = index + 1
    })
  }

  return {
    generateProblems
  }
}