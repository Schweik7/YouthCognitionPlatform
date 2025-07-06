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
  max-width: 700px;
  margin: 0 auto;
  text-align: left;
  line-height: 1.6;
}

.instruction h2 {
  text-align: center;
  color: #409EFF;
  margin-bottom: 20px;
}

.continue-btn {
  margin: 20px auto;
  display: block;
  min-width: 120px;
  font-weight: bold;
}
</style>