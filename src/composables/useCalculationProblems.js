export function useCalculationProblems() {
  
  const generateProblems = (gradeLevel) => {
    const problems = []

    if (gradeLevel === 1) {
      // 一年级：0-10的加减法，加法减法各20题
      generateGrade1Problems(problems)
    } else if (gradeLevel === 2) {
      // 二年级：两位数的加减法
      generateGrade2Problems(problems)
    } else if (gradeLevel === 3) {
      // 三年级：三位数运算
      generateGrade3Problems(problems)
    } else if (gradeLevel === 4) {
      // 四年级：乘除法运算
      generateGrade4Problems(problems)
    } else if (gradeLevel === 5) {
      // 五年级：多位数乘除法、小数运算
      generateGrade5Problems(problems)
    } else if (gradeLevel === 6) {
      // 六年级：分数运算、比例运算
      generateGrade6Problems(problems)
    }

    // 随机打乱题目顺序
    shuffleProblems(problems)
    
    return problems
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

  const simplifyFraction = (numerator, denominator) => {
    const divisor = gcd(numerator, denominator)
    return {
      numerator: numerator / divisor,
      denominator: denominator / divisor
    }
  }

  const toMixedNumber = (numerator, denominator) => {
    const whole = Math.floor(numerator / denominator)
    const remainder = numerator % denominator
    return {
      whole: whole,
      numerator: remainder,
      denominator: denominator
    }
  }

  const generateFractionAddSub = () => {
    // 生成两个分数相加减，使用通分
    const denominator = Math.floor(Math.random() * 6) + 2  // 2-7
    const numerator1 = Math.floor(Math.random() * denominator) + 1  // 1 到 denominator-1
    const numerator2 = Math.floor(Math.random() * denominator) + 1  // 1 到 denominator-1
    
    const isAddition = Math.random() < 0.5
    let resultNumerator
    
    if (isAddition) {
      resultNumerator = numerator1 + numerator2
    } else {
      // 确保结果不为负数
      if (numerator1 >= numerator2) {
        resultNumerator = numerator1 - numerator2
      } else {
        resultNumerator = numerator2 - numerator1
      }
    }
    
    // 约分
    const simplified = simplifyFraction(resultNumerator, denominator)
    
    // 转换为带分数
    const mixed = toMixedNumber(simplified.numerator, simplified.denominator)
    
    return {
      text: `${numerator1}/${denominator} ${isAddition ? '+' : '-'} ${numerator2}/${denominator} = `,
      answer: mixed.whole + mixed.numerator / mixed.denominator,
      fractionAnswer: mixed
    }
  }

  const generateFractionIntegerAddSub = () => {
    // 生成分数与整数相加减
    const denominator = Math.floor(Math.random() * 6) + 2  // 2-7
    const numerator = Math.floor(Math.random() * denominator) + 1  // 1 到 denominator-1
    const integer = Math.floor(Math.random() * 5) + 1  // 1-5
    
    const isAddition = Math.random() < 0.5
    let resultNumerator
    
    if (isAddition) {
      resultNumerator = numerator + integer * denominator
    } else {
      // 确保结果不为负数
      if (integer * denominator >= numerator) {
        resultNumerator = integer * denominator - numerator
      } else {
        resultNumerator = numerator + integer * denominator  // 改为加法避免负数
      }
    }
    
    // 约分
    const simplified = simplifyFraction(resultNumerator, denominator)
    
    // 转换为带分数
    const mixed = toMixedNumber(simplified.numerator, simplified.denominator)
    
    return {
      text: `${numerator}/${denominator} ${isAddition ? '+' : '-'} ${integer} = `,
      answer: mixed.whole + mixed.numerator / mixed.denominator,
      fractionAnswer: mixed
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
        a = Math.floor(Math.random() * 90) + 10
        b = Math.floor(Math.random() * (a + 1))
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
        a = Math.floor(Math.random() * 900) + 100
        b = Math.floor(Math.random() * 90) + 10
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

    // 第三部分：10道分数加减法（8道分数+分数，2道分数+整数）
    for (let i = 0; i < 10; i++) {
      let fractionProblem
      if (i < 8) {
        // 两个分数相加减
        fractionProblem = generateFractionAddSub()
      } else {
        // 分数和整数相加减
        fractionProblem = generateFractionIntegerAddSub()
      }
      
      problems.push({
        index: i + 21,
        text: fractionProblem.text,
        answer: fractionProblem.answer,
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
    for (let i = problems.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1))
      ;[problems[i], problems[j]] = [problems[j], problems[i]]
    }
    
    // 重新设置题目序号
    problems.forEach((problem, index) => {
      problem.index = index + 1
    })
  }

  return {
    generateProblems
  }
}