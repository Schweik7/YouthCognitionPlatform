/**
 * 数字格式化工具
 * 支持循环小数和带分数的显示
 */

/**
 * 格式化答案显示
 * @param {string|number} answer - 答案
 * @returns {string} - 格式化后的答案
 */
export function formatAnswer(answer) {
  if (typeof answer === 'string') {
    // 处理带分数格式 "整数又分子/分母"
    if (answer.includes('又')) {
      return formatMixedNumber(answer)
    }
    
    // 处理循环小数格式 "数字.循环部分̄"
    if (answer.includes('̄')) {
      return formatRepeatingDecimal(answer)
    }
    
    // 处理普通分数格式 "分子/分母"
    if (answer.includes('/') && !answer.includes('又')) {
      return formatFraction(answer)
    }
  }
  
  return String(answer)
}

/**
 * 格式化带分数显示
 * @param {string} mixedNumber - 带分数字符串，如 "2又3/4"
 * @returns {string} - HTML格式的带分数
 */
export function formatMixedNumber(mixedNumber) {
  const parts = mixedNumber.split('又')
  if (parts.length !== 2) return mixedNumber
  
  const whole = parts[0].trim()
  const fraction = parts[1].trim()
  
  if (fraction.includes('/')) {
    const [numerator, denominator] = fraction.split('/')
    return `${whole}<span class="mixed-number"><sup>${numerator}</sup>/<sub>${denominator}</sub></span>`
  }
  
  return mixedNumber
}

/**
 * 格式化普通分数显示
 * @param {string} fraction - 分数字符串，如 "3/4"
 * @returns {string} - HTML格式的分数
 */
export function formatFraction(fraction) {
  if (fraction.includes('/')) {
    const [numerator, denominator] = fraction.split('/')
    return `<span class="fraction"><sup>${numerator}</sup>/<sub>${denominator}</sub></span>`
  }
  
  return fraction
}

/**
 * 格式化循环小数显示
 * @param {string} repeatingDecimal - 循环小数字符串，如 "8.1̄3̄"
 * @returns {string} - HTML格式的循环小数
 */
export function formatRepeatingDecimal(repeatingDecimal) {
  // 将循环部分用上划线标记
  let formatted = repeatingDecimal.replace(/([0-9])̄/g, '<span class="repeating">$1</span>')
  return formatted
}

/**
 * 检查答案是否为分数格式
 * @param {string|number} answer - 答案
 * @returns {boolean} - 是否为分数
 */
export function isFraction(answer) {
  return typeof answer === 'string' && (answer.includes('/') || answer.includes('又'))
}

/**
 * 检查答案是否为循环小数格式
 * @param {string|number} answer - 答案
 * @returns {boolean} - 是否为循环小数
 */
export function isRepeatingDecimal(answer) {
  return typeof answer === 'string' && answer.includes('̄')
}

/**
 * 比较两个答案是否相等（考虑特殊格式）
 * @param {string|number} userAnswer - 用户答案
 * @param {string|number} correctAnswer - 正确答案
 * @returns {boolean} - 是否相等
 */
export function compareAnswers(userAnswer, correctAnswer) {
  // 如果都是普通数字，直接比较
  if (typeof userAnswer === 'number' && typeof correctAnswer === 'number') {
    return Math.abs(userAnswer - correctAnswer) < 0.001
  }
  
  // 转换为字符串进行比较
  const userStr = String(userAnswer).trim()
  const correctStr = String(correctAnswer).trim()
  
  // 直接字符串比较
  if (userStr === correctStr) {
    return true
  }
  
  // 尝试转换为数值比较（如果可能）
  try {
    const userNum = parseFloat(userStr)
    const correctNum = parseFloat(correctStr)
    if (!isNaN(userNum) && !isNaN(correctNum)) {
      return Math.abs(userNum - correctNum) < 0.001
    }
  } catch (e) {
    // 忽略转换错误
  }
  
  return false
}