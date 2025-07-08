<template>
  <div class="type-stats">
    <h3>题型分析</h3>
    
    <!-- 一年级题型统计 -->
    <el-row v-if="gradeLevel === 1" :gutter="20">
      <el-col :span="12">
        <el-card class="type-card">
          <template #header>
            <div class="type-header">加法题</div>
          </template>
          <div class="type-stats-content">
            <div class="type-stat-item">
              <span>总数量:</span>
              <span>{{ typeStats.addition.total }}</span>
            </div>
            <div class="type-stat-item">
              <span>已完成:</span>
              <span>{{ typeStats.addition.completed }}</span>
            </div>
            <div class="type-stat-item">
              <span>正确数量:</span>
              <span>{{ typeStats.addition.correct }}</span>
            </div>
            <div class="type-stat-item">
              <span>正确率:</span>
              <span>{{ formatPercentage(typeStats.addition.accuracy) }}%</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="type-card">
          <template #header>
            <div class="type-header">减法题</div>
          </template>
          <div class="type-stats-content">
            <div class="type-stat-item">
              <span>总数量:</span>
              <span>{{ typeStats.subtraction.total }}</span>
            </div>
            <div class="type-stat-item">
              <span>已完成:</span>
              <span>{{ typeStats.subtraction.completed }}</span>
            </div>
            <div class="type-stat-item">
              <span>正确数量:</span>
              <span>{{ typeStats.subtraction.correct }}</span>
            </div>
            <div class="type-stat-item">
              <span>正确率:</span>
              <span>{{ formatPercentage(typeStats.subtraction.accuracy) }}%</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 二年级题型统计 -->
    <el-row v-else-if="gradeLevel === 2" :gutter="20">
      <el-col :span="12">
        <el-card class="type-card">
          <template #header>
            <div class="type-header">两数加减法</div>
          </template>
          <div class="type-stats-content">
            <div class="type-stat-item">
              <span>总数量:</span>
              <span>{{ typeStats.twoNumbers.total }}</span>
            </div>
            <div class="type-stat-item">
              <span>已完成:</span>
              <span>{{ typeStats.twoNumbers.completed }}</span>
            </div>
            <div class="type-stat-item">
              <span>正确数量:</span>
              <span>{{ typeStats.twoNumbers.correct }}</span>
            </div>
            <div class="type-stat-item">
              <span>正确率:</span>
              <span>{{ formatPercentage(typeStats.twoNumbers.accuracy) }}%</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="type-card">
          <template #header>
            <div class="type-header">三数加减法</div>
          </template>
          <div class="type-stats-content">
            <div class="type-stat-item">
              <span>总数量:</span>
              <span>{{ typeStats.threeNumbers.total }}</span>
            </div>
            <div class="type-stat-item">
              <span>已完成:</span>
              <span>{{ typeStats.threeNumbers.completed }}</span>
            </div>
            <div class="type-stat-item">
              <span>正确数量:</span>
              <span>{{ typeStats.threeNumbers.correct }}</span>
            </div>
            <div class="type-stat-item">
              <span>正确率:</span>
              <span>{{ formatPercentage(typeStats.threeNumbers.accuracy) }}%</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 三年级题型统计 -->
    <el-row v-else-if="gradeLevel === 3" :gutter="20">
      <el-col :span="8">
        <el-card class="type-card">
          <template #header>
            <div class="type-header">三位数和两位数加减法</div>
          </template>
          <div class="type-stats-content">
            <div class="type-stat-item">
              <span>总数量:</span>
              <span>{{ typeStats.type1.total }}</span>
            </div>
            <div class="type-stat-item">
              <span>已完成:</span>
              <span>{{ typeStats.type1.completed }}</span>
            </div>
            <div class="type-stat-item">
              <span>正确数量:</span>
              <span>{{ typeStats.type1.correct }}</span>
            </div>
            <div class="type-stat-item">
              <span>正确率:</span>
              <span>{{ formatPercentage(typeStats.type1.accuracy) }}%</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="type-card">
          <template #header>
            <div class="type-header">三位数与三位数加减法</div>
          </template>
          <div class="type-stats-content">
            <div class="type-stat-item">
              <span>总数量:</span>
              <span>{{ typeStats.type2.total }}</span>
            </div>
            <div class="type-stat-item">
              <span>已完成:</span>
              <span>{{ typeStats.type2.completed }}</span>
            </div>
            <div class="type-stat-item">
              <span>正确数量:</span>
              <span>{{ typeStats.type2.correct }}</span>
            </div>
            <div class="type-stat-item">
              <span>正确率:</span>
              <span>{{ formatPercentage(typeStats.type2.accuracy) }}%</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="type-card">
          <template #header>
            <div class="type-header">三位数三数加减法</div>
          </template>
          <div class="type-stats-content">
            <div class="type-stat-item">
              <span>总数量:</span>
              <span>{{ typeStats.type3.total }}</span>
            </div>
            <div class="type-stat-item">
              <span>已完成:</span>
              <span>{{ typeStats.type3.completed }}</span>
            </div>
            <div class="type-stat-item">
              <span>正确数量:</span>
              <span>{{ typeStats.type3.correct }}</span>
            </div>
            <div class="type-stat-item">
              <span>正确率:</span>
              <span>{{ formatPercentage(typeStats.type3.accuracy) }}%</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 四年级题型统计 -->
    <el-row v-else-if="gradeLevel === 4" :gutter="20">
      <el-col :span="6">
        <el-card class="type-card">
          <template #header>
            <div class="type-header">两位数加减法</div>
          </template>
          <div class="type-stats-content">
            <div class="type-stat-item">
              <span>总数量:</span>
              <span>{{ typeStats.twoDigitAddSub?.total || 0 }}</span>
            </div>
            <div class="type-stat-item">
              <span>已完成:</span>
              <span>{{ typeStats.twoDigitAddSub?.completed || 0 }}</span>
            </div>
            <div class="type-stat-item">
              <span>正确数量:</span>
              <span>{{ typeStats.twoDigitAddSub?.correct || 0 }}</span>
            </div>
            <div class="type-stat-item">
              <span>正确率:</span>
              <span>{{ formatPercentage(typeStats.twoDigitAddSub?.accuracy || 0) }}%</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="type-card">
          <template #header>
            <div class="type-header">两位数乘法</div>
          </template>
          <div class="type-stats-content">
            <div class="type-stat-item">
              <span>总数量:</span>
              <span>{{ typeStats.twoDigitMult?.total || 0 }}</span>
            </div>
            <div class="type-stat-item">
              <span>已完成:</span>
              <span>{{ typeStats.twoDigitMult?.completed || 0 }}</span>
            </div>
            <div class="type-stat-item">
              <span>正确数量:</span>
              <span>{{ typeStats.twoDigitMult?.correct || 0 }}</span>
            </div>
            <div class="type-stat-item">
              <span>正确率:</span>
              <span>{{ formatPercentage(typeStats.twoDigitMult?.accuracy || 0) }}%</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="type-card">
          <template #header>
            <div class="type-header">分数加减法</div>
          </template>
          <div class="type-stats-content">
            <div class="type-stat-item">
              <span>总数量:</span>
              <span>{{ typeStats.fractionAddSub?.total || 0 }}</span>
            </div>
            <div class="type-stat-item">
              <span>已完成:</span>
              <span>{{ typeStats.fractionAddSub?.completed || 0 }}</span>
            </div>
            <div class="type-stat-item">
              <span>正确数量:</span>
              <span>{{ typeStats.fractionAddSub?.correct || 0 }}</span>
            </div>
            <div class="type-stat-item">
              <span>正确率:</span>
              <span>{{ formatPercentage(typeStats.fractionAddSub?.accuracy || 0) }}%</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="type-card">
          <template #header>
            <div class="type-header">三位数乘法</div>
          </template>
          <div class="type-stats-content">
            <div class="type-stat-item">
              <span>总数量:</span>
              <span>{{ typeStats.threeDigitMult?.total || 0 }}</span>
            </div>
            <div class="type-stat-item">
              <span>已完成:</span>
              <span>{{ typeStats.threeDigitMult?.completed || 0 }}</span>
            </div>
            <div class="type-stat-item">
              <span>正确数量:</span>
              <span>{{ typeStats.threeDigitMult?.correct || 0 }}</span>
            </div>
            <div class="type-stat-item">
              <span>正确率:</span>
              <span>{{ formatPercentage(typeStats.threeDigitMult?.accuracy || 0) }}%</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 五年级及以上题型统计 -->
    <el-row v-else-if="gradeLevel >= 5" :gutter="20">
      <el-col :span="8">
        <el-card class="type-card">
          <template #header>
            <div class="type-header">乘法题</div>
          </template>
          <div class="type-stats-content">
            <div class="type-stat-item">
              <span>总数量:</span>
              <span>{{ typeStats.multiplication?.total || 0 }}</span>
            </div>
            <div class="type-stat-item">
              <span>已完成:</span>
              <span>{{ typeStats.multiplication?.completed || 0 }}</span>
            </div>
            <div class="type-stat-item">
              <span>正确数量:</span>
              <span>{{ typeStats.multiplication?.correct || 0 }}</span>
            </div>
            <div class="type-stat-item">
              <span>正确率:</span>
              <span>{{ formatPercentage(typeStats.multiplication?.accuracy || 0) }}%</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="type-card">
          <template #header>
            <div class="type-header">除法题</div>
          </template>
          <div class="type-stats-content">
            <div class="type-stat-item">
              <span>总数量:</span>
              <span>{{ typeStats.division?.total || 0 }}</span>
            </div>
            <div class="type-stat-item">
              <span>已完成:</span>
              <span>{{ typeStats.division?.completed || 0 }}</span>
            </div>
            <div class="type-stat-item">
              <span>正确数量:</span>
              <span>{{ typeStats.division?.correct || 0 }}</span>
            </div>
            <div class="type-stat-item">
              <span>正确率:</span>
              <span>{{ formatPercentage(typeStats.division?.accuracy || 0) }}%</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="type-card">
          <template #header>
            <div class="type-header">混合运算</div>
          </template>
          <div class="type-stats-content">
            <div class="type-stat-item">
              <span>总数量:</span>
              <span>{{ typeStats.mixed?.total || 0 }}</span>
            </div>
            <div class="type-stat-item">
              <span>已完成:</span>
              <span>{{ typeStats.mixed?.completed || 0 }}</span>
            </div>
            <div class="type-stat-item">
              <span>正确数量:</span>
              <span>{{ typeStats.mixed?.correct || 0 }}</span>
            </div>
            <div class="type-stat-item">
              <span>正确率:</span>
              <span>{{ formatPercentage(typeStats.mixed?.accuracy || 0) }}%</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
defineProps({
  gradeLevel: {
    type: Number,
    required: true
  },
  typeStats: {
    type: Object,
    required: true
  },
  formatPercentage: {
    type: Function,
    required: true
  }
})
</script>

<style scoped>
.type-stats {
  margin-top: 30px;
  width: 100%;
}

.type-stats h3 {
  margin-bottom: 20px;
  color: #409EFF;
}

.type-card {
  height: 100%;
}

.type-header {
  font-weight: bold;
  color: #303133;
}

.type-stats-content {
  padding: 10px 0;
}

.type-stat-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px dashed #ebeef5;
}

.type-stat-item:last-child {
  border-bottom: none;
}
</style>