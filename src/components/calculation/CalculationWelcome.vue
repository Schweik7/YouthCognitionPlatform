<template>
  <div class="instruction">
    <h2>计算流畅性测试</h2>
    <p>欢迎参加计算流畅性测试，这个测试将评估你的计算能力和速度。</p>
    <p>在测试中，你将看到一系列计算题目，需要输入正确的答案。</p>
    <p>请认真完成测试，尽可能快速准确地计算出答案。</p>
    <p v-if="gradeLevel === 1">一年级的题目为0到10，两个数的加减法，加法减法各20题。</p>
    <p v-if="gradeLevel === 2">二年级的题目为两位数的加减法；包括30道两个数的加减法和10道三个数的加减法。</p>
    <p v-if="gradeLevel === 3">三年级的题目包括三位数和两位数的加减法，三位数与三位数的加减法，以及三位数三个数的加减法。</p>
    <p v-if="gradeLevel === 4">四年级的题目包括乘除法运算，包括两位数乘一位数、三位数除一位数等。</p>
    <p v-if="gradeLevel === 5">五年级的题目包括多位数乘除法、小数运算等复杂计算。</p>
    <p v-if="gradeLevel === 6">六年级的题目包括分数运算、比例运算等高级计算。</p>
    <el-button type="primary" class="continue-btn" @click="$emit('start')">开始测试</el-button>
  </div>
</template>

<script setup>
defineProps({
  gradeLevel: {
    type: Number,
    default: 1
  }
})

defineEmits(['start'])
</script>

<style scoped>
.instruction {
  max-width: 760px;
  margin: clamp(16px, 5vh, 56px) auto;
  padding: clamp(30px, 4vw, 50px) clamp(24px, 4vw, 54px);
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-xl);
  box-shadow: var(--sh-md);
  text-align: left;
  line-height: 1.95;
  font-size: 16px;
  color: var(--ink-700);
}

.instruction h2 {
  position: relative;
  text-align: center;
  color: var(--ink-900);
  margin-bottom: 28px;
  padding-bottom: 18px;
  font-size: clamp(23px, 2.8vw, 29px);
}

.instruction h2::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: 0;
  transform: translateX(-50%);
  width: 54px;
  height: 4px;
  border-radius: var(--r-full);
  background: linear-gradient(90deg, #b79bfb, var(--hue-calc));
}

.instruction p {
  margin: 0 0 12px;
  padding-left: 22px;
  position: relative;
}

.instruction p::before {
  content: '';
  position: absolute;
  left: 2px;
  top: 14px;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--hue-calc);
  opacity: .5;
}

/* 年级说明单独强调 */
.instruction p:last-of-type {
  margin-top: 18px;
  padding: 16px 20px 16px 42px;
  background: linear-gradient(135deg, rgba(139, 92, 246, .08), rgba(76, 111, 255, .05));
  border: 1px solid rgba(139, 92, 246, .18);
  border-radius: var(--r-md);
  color: var(--ink-900);
  font-weight: 600;
}

.instruction p:last-of-type::before { left: 20px; top: 26px; }

.continue-btn {
  margin: 34px auto 0;
  display: block;
  min-width: 190px;
  font-weight: 700;
  letter-spacing: .08em;
}
</style>
