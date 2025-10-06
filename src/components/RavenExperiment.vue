<template>
    <div class="experiment-page">
        <TopNavBar />
        <div class="experiment-container">
            <!-- 调试面板 -->
            <div v-if="debugMode" class="debug-panel">
                <h3>调试模式</h3>
                <div class="debug-controls">
                    <el-input-number v-model="remainingTime" :min="0" :max="1200" label="剩余时间(秒)"></el-input-number>
                    <el-button type="primary" @click="updateTimer">更新时间</el-button>
                    <el-button type="warning" @click="submitTest">提交测试</el-button>
                </div>
            </div>

            <!-- 实验内容区域 -->
            <div class="content-area" :class="{ 'sidebar-collapsed': !sidebarVisible }">
                <!-- 指导语阶段 -->
                <div v-if="phase === 'welcome'" class="instruction">
                    <h2>图形推理测试</h2>
                    <p>欢迎参加图形推理测试（瑞文智力测验），这个测试将评估你的图形推理和逻辑思维能力。</p>
                    <p>测试共72题，分为6组（A、AB、B、C、D、E），每组12题。</p>
                    <p>每道题上方会显示一个图形，下方有若干选项，请选择最合适的选项来完成图形。</p>
                    <p>测试时间为20分钟。请认真完成每一题。</p>
                    <el-button type="primary" class="continue-btn" @click="nextPhase">开始测试</el-button>
                </div>

                <!-- 测试阶段 -->
                <div v-else-if="phase === 'test'" class="test-container">
                    <!-- 顶部信息栏 -->
                    <div class="test-header">
                        <div class="test-info">
                            <span>题目 {{ currentQuestionIndex + 1 }} / 72</span>
                            <span class="group-info">{{ currentGroup }}组 ({{ currentQuestionInGroup }}/12)</span>
                        </div>
                        <div class="test-timer" :class="{ 'timer-warning': remainingTime < 300 }">
                            <i class="el-icon-time"></i>
                            {{ formatTime(remainingTime) }}
                        </div>
                    </div>

                    <!-- 题目区域 -->
                    <div class="question-area">
                        <!-- 主图片 -->
                        <div class="main-image-container">
                            <img
                                v-if="currentQuestion"
                                :src="currentQuestion.main_image_url"
                                :alt="`题目${currentQuestion.question_id}`"
                                class="main-image"
                                @error="handleImageError"
                            />
                        </div>

                        <!-- 选项区域 -->
                        <div class="options-container">
                            <div class="options-grid" :class="{ 'options-8': currentNumOptions === 8 }">
                                <div
                                    v-for="(url, index) in currentOptionUrls"
                                    :key="index"
                                    class="option-item"
                                    :class="{ 'selected': currentUserAnswer === (index + 1) }"
                                    @click="selectOption(index + 1)"
                                >
                                    <img
                                        :src="url"
                                        :alt="`选项${index + 1}`"
                                        class="option-image"
                                        @error="handleImageError"
                                    />
                                    <div class="option-label">{{ index + 1 }}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 导航按钮 -->
                    <div class="navigation-buttons">
                        <el-button @click="previousQuestion" :disabled="currentQuestionIndex === 0">
                            <i class="el-icon-arrow-left"></i> 上一题
                        </el-button>
                        <el-button type="primary" @click="nextQuestion" v-if="currentQuestionIndex < 71">
                            下一题 <i class="el-icon-arrow-right"></i>
                        </el-button>
                        <el-button type="success" @click="confirmSubmit" v-else>
                            <i class="el-icon-check"></i> 提交测试
                        </el-button>
                    </div>
                </div>

                <!-- 结果阶段 -->
                <div v-else-if="phase === 'result'" class="result-container">
                    <h2>测试结果</h2>

                    <el-card class="result-card">
                        <div class="result-item">
                            <div class="result-label">完成题数:</div>
                            <div class="result-value">{{ testResults.answeredQuestions }} / 72</div>
                        </div>
                        <div class="result-item">
                            <div class="result-label">正确题数:</div>
                            <div class="result-value">{{ testResults.correctAnswers }}</div>
                        </div>
                        <div class="result-item total-score">
                            <div class="result-label">原始分数:</div>
                            <div class="result-value">{{ testResults.rawScore }}</div>
                        </div>
                        <div class="result-item" v-if="testResults.iq">
                            <div class="result-label">智商 (IQ):</div>
                            <div class="result-value highlight">{{ testResults.iq }}</div>
                        </div>
                        <div class="result-item" v-if="testResults.percentile">
                            <div class="result-label">百分位:</div>
                            <div class="result-value">{{ testResults.percentile }}</div>
                        </div>
                        <div class="result-item" v-if="testResults.zScore">
                            <div class="result-label">Z分数:</div>
                            <div class="result-value">{{ testResults.zScore }}</div>
                        </div>
                        <div class="result-item">
                            <div class="result-label">用时:</div>
                            <div class="result-value">{{ formatTime(testResults.totalTime) }}</div>
                        </div>
                    </el-card>

                    <div class="action-buttons">
                        <el-button type="primary" @click="goToSelection">返回测试选择</el-button>
                    </div>
                </div>
            </div>

            <!-- 侧边栏（可折叠的题目面板） -->
            <div class="sidebar" :class="{ 'collapsed': !sidebarVisible }" v-if="phase === 'test'">
                <el-button
                    class="sidebar-toggle"
                    @click="sidebarVisible = !sidebarVisible"
                    circle
                >
                    <span v-if="sidebarVisible">←</span>
                    <span v-else>→</span>
                </el-button>

                <div class="sidebar-content">
                    <h3>答题情况</h3>
                    <div v-for="(group, groupIndex) in groups" :key="group" class="group-panel">
                        <div class="group-header">{{ group }}组</div>
                        <div class="questions-grid">
                            <div
                                v-for="i in 12"
                                :key="i"
                                class="question-cell"
                                :class="{
                                    'answered': isQuestionAnswered(groupIndex * 12 + i - 1),
                                    'current': currentQuestionIndex === (groupIndex * 12 + i - 1)
                                }"
                                @click="jumpToQuestion(groupIndex * 12 + i - 1)"
                            >
                                {{ i }}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus';
import TopNavBar from './TopNavBar.vue';

const router = useRouter();

// 状态变量
const phase = ref('welcome'); // 实验阶段: welcome, test, result
const userId = ref(null);
const testSessionId = ref(null);
const questions = ref([]); // 所有题目信息
const userAnswers = ref({}); // 用户答案 {question_id: answer}
const currentQuestionIndex = ref(0); // 当前题目索引（0-71）
const remainingTime = ref(1200); // 20分钟倒计时
const timerInterval = ref(null);
const debugMode = ref(false);
const sidebarVisible = ref(true);

const testResults = ref({
    answeredQuestions: 0,
    correctAnswers: 0,
    rawScore: 0,
    percentile: null,
    zScore: null,
    iq: null,
    totalTime: 0
});

// 题目分组
const groups = ['A', 'AB', 'B', 'C', 'D', 'E'];

// 当前题目
const currentQuestion = computed(() => {
    if (questions.value.length > 0 && currentQuestionIndex.value < questions.value.length) {
        return questions.value[currentQuestionIndex.value];
    }
    return null;
});

// 当前组名
const currentGroup = computed(() => {
    if (currentQuestion.value) {
        return currentQuestion.value.group_name;
    }
    return '';
});

// 组内题号
const currentQuestionInGroup = computed(() => {
    if (currentQuestion.value) {
        return currentQuestion.value.question_in_group;
    }
    return 0;
});

// 当前选项数量
const currentNumOptions = computed(() => {
    if (currentQuestion.value) {
        return currentQuestion.value.num_options;
    }
    return 6;
});

// 当前选项URLs
const currentOptionUrls = computed(() => {
    if (currentQuestion.value) {
        return currentQuestion.value.option_image_urls;
    }
    return [];
});

// 当前用户答案
const currentUserAnswer = computed(() => {
    if (currentQuestion.value) {
        return userAnswers.value[currentQuestion.value.question_id];
    }
    return null;
});

// 格式化时间显示
const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
};

// 更新计时器
const updateTimer = () => {
    if (phase.value !== 'test') return;

    remainingTime.value--;

    if (remainingTime.value <= 0) {
        clearInterval(timerInterval.value);
        ElMessage.warning('测试时间已到，自动提交');
        submitTest();
    }
};

// 启动倒计时
const startTimer = () => {
    if (timerInterval.value) clearInterval(timerInterval.value);
    timerInterval.value = setInterval(updateTimer, 1000);
};

// 获取用户信息
const getUserInfo = async () => {
    const userInfoStr = localStorage.getItem('userInfo');
    if (!userInfoStr) {
        ElMessage.warning('未登录，请先登录');
        router.push('/');
        return;
    }

    try {
        const userInfo = JSON.parse(userInfoStr);
        userId.value = userInfo.id;
    } catch (error) {
        console.error('解析用户信息失败:', error);
    }
};

// 创建测试会话
const createTestSession = async () => {
    if (!userId.value) {
        console.error('无法创建测试会话：缺少用户ID');
        return;
    }

    try {
        const response = await fetch('/api/raven-test/sessions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId.value
            })
        });

        if (response.ok) {
            const data = await response.json();
            testSessionId.value = data.id;
            console.log('测试会话创建成功，ID:', testSessionId.value);
        } else {
            console.error('创建测试会话失败:', await response.text());
        }
    } catch (error) {
        console.error('创建测试会话请求失败:', error);
    }
};

// 获取所有题目
const fetchQuestions = async () => {
    const loading = ElLoading.service({
        lock: true,
        text: '正在加载题目...',
        background: 'rgba(0, 0, 0, 0.7)'
    });

    try {
        const url = testSessionId.value
            ? `/api/raven-test/questions?test_session_id=${testSessionId.value}`
            : '/api/raven-test/questions';

        const response = await fetch(url);
        if (response.ok) {
            const data = await response.json();
            questions.value = data;

            // 如果有已保存的答案，加载到userAnswers中
            data.forEach(q => {
                if (q.user_answer) {
                    userAnswers.value[q.question_id] = q.user_answer;
                }
            });

            console.log('题目加载成功，共', data.length, '题');
        } else {
            ElMessage.error('获取题目失败');
        }
    } catch (error) {
        console.error('获取题目失败:', error);
        ElMessage.error('网络错误，无法获取题目');
    } finally {
        loading.close();
    }
};

// 选择选项
const selectOption = async (optionNumber) => {
    if (!currentQuestion.value) return;

    const questionId = currentQuestion.value.question_id;
    userAnswers.value[questionId] = optionNumber;

    // 立即保存到服务器
    await saveAnswer(questionId, optionNumber);

    // 自动跳转到下一题（如果不是最后一题）
    if (currentQuestionIndex.value < 71) {
        setTimeout(() => {
            nextQuestion();
        }, 300);
    }
};

// 保存答案到服务器
const saveAnswer = async (questionId, userAnswer) => {
    if (!testSessionId.value || !userId.value) {
        return;
    }

    try {
        const response = await fetch('/api/raven-test/answers', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId.value,
                test_session_id: testSessionId.value,
                question_id: questionId,
                user_answer: userAnswer,
                response_time: null
            })
        });

        if (!response.ok) {
            console.error('保存答案失败:', await response.text());
        }
    } catch (error) {
        console.error('保存答案请求失败:', error);
    }
};

// 上一题
const previousQuestion = () => {
    if (currentQuestionIndex.value > 0) {
        currentQuestionIndex.value--;
    }
};

// 下一题
const nextQuestion = () => {
    if (currentQuestionIndex.value < 71) {
        currentQuestionIndex.value++;
    }
};

// 跳转到指定题目
const jumpToQuestion = (index) => {
    currentQuestionIndex.value = index;
};

// 判断题目是否已答
const isQuestionAnswered = (index) => {
    if (questions.value.length > 0 && index < questions.value.length) {
        const questionId = questions.value[index].question_id;
        return userAnswers.value[questionId] !== undefined;
    }
    return false;
};

// 确认提交
const confirmSubmit = async () => {
    const answeredCount = Object.keys(userAnswers.value).length;
    const unansweredCount = 72 - answeredCount;

    let message = `您已完成 ${answeredCount} 题。`;
    if (unansweredCount > 0) {
        message += `还有 ${unansweredCount} 题未完成。`;
    }
    message += '确定要提交测试吗？';

    try {
        await ElMessageBox.confirm(message, '提交确认', {
            confirmButtonText: '确定提交',
            cancelButtonText: '继续答题',
            type: 'warning',
        });
        await submitTest();
    } catch {
        // 用户取消提交
    }
};

// 提交测试
const submitTest = async () => {
    clearInterval(timerInterval.value);

    const loading = ElLoading.service({
        lock: true,
        text: '正在处理结果...',
        background: 'rgba(0, 0, 0, 0.7)'
    });

    try {
        // 完成测试会话
        const response = await fetch(`/api/raven-test/sessions/${testSessionId.value}/complete`, {
            method: 'POST'
        });

        if (response.ok) {
            const resultsResponse = await fetch(`/api/raven-test/sessions/${testSessionId.value}/results`);

            if (resultsResponse.ok) {
                const data = await resultsResponse.json();

                // 设置测试结果
                testResults.value = {
                    answeredQuestions: data.stats.answeredQuestions,
                    correctAnswers: data.stats.correctAnswers,
                    rawScore: data.stats.rawScore,
                    percentile: data.stats.percentile,
                    zScore: data.stats.zScore,
                    iq: data.stats.iq,
                    totalTime: data.stats.totalTimeSeconds || (1200 - remainingTime.value)
                };

                // 显示结果页面
                phase.value = 'result';
            } else {
                console.error('获取测试结果失败:', await resultsResponse.text());
                ElMessage.error('获取测试结果失败');
            }
        } else {
            console.error('完成测试会话失败:', await response.text());
            ElMessage.error('完成测试失败');
        }
    } catch (error) {
        console.error('提交测试请求失败:', error);
        ElMessage.error('网络错误，无法提交测试');
    } finally {
        loading.close();
    }
};

// 返回测试选择
const goToSelection = () => {
    router.push('/selection');
};

// 进入下一阶段
const nextPhase = async () => {
    if (phase.value === 'welcome') {
        // 获取用户信息
        await getUserInfo();

        // 创建测试会话
        await createTestSession();

        // 获取所有题目
        await fetchQuestions();

        // 进入测试阶段
        phase.value = 'test';

        // 启动计时器
        startTimer();
    }
};

// 图片加载错误处理
const handleImageError = (event) => {
    console.error('图片加载失败:', event.target.src);
    event.target.alt = '图片加载失败';
};

// 键盘监听函数
const keyHandler = (e) => {
    // Alt+[ 或 Alt+] 切换调试模式
    if ((e.key === '[' && e.altKey) || (e.key === ']' && e.altKey)) {
        debugMode.value = !debugMode.value;
        return;
    }

    // 测试阶段的键盘快捷键
    if (phase.value === 'test') {
        // 数字键1-8选择选项
        if (e.key >= '1' && e.key <= '8') {
            const optionNum = parseInt(e.key);
            if (optionNum <= currentNumOptions.value) {
                selectOption(optionNum);
            }
        }
        // 左右箭头切换题目
        else if (e.key === 'ArrowLeft') {
            previousQuestion();
        } else if (e.key === 'ArrowRight') {
            nextQuestion();
        }
    }
};

// 生命周期钩子
onMounted(() => {
    // 添加键盘事件监听
    window.addEventListener('keydown', keyHandler);

    // 确保初始滚动位置在页面顶部
    window.scrollTo(0, 0);
});

onUnmounted(() => {
    // 清理资源
    window.removeEventListener('keydown', keyHandler);
    clearInterval(timerInterval.value);
});
</script>

<style scoped>
/* 全局样式 */
.experiment-page {
    min-height: 100vh;
    background-color: #f5f7fa;
}

.experiment-container {
    display: flex;
    min-height: calc(100vh - 60px);
    position: relative;
    justify-content: center; /* 内容居中 */
}

.content-area {
    flex: 1;
    max-width: 1200px; /* 限制最大宽度，确保居中 */
    padding: 20px;
    box-sizing: border-box;
}

/* 调试面板 */
.debug-panel {
    position: fixed;
    top: 60px;
    left: 0;
    background-color: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 10px;
    z-index: 1000;
    border-radius: 0 0 5px 0;
}

.debug-controls {
    display: flex;
    gap: 10px;
    align-items: center;
    flex-wrap: wrap;
}

/* 指导语样式 */
.instruction {
    max-width: 800px;
    margin: 0 auto;
    text-align: left;
    line-height: 1.8;
    padding: 40px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.instruction h2 {
    text-align: center;
    color: #409EFF;
    margin-bottom: 30px;
    font-size: 28px;
}

.instruction p {
    margin-bottom: 15px;
    font-size: 16px;
}

.continue-btn {
    margin: 30px auto 0;
    display: block;
    min-width: 150px;
    font-weight: bold;
    font-size: 16px;
}

/* 测试容器 */
.test-container {
    max-width: 1200px;
    margin: 0 auto;
    height: calc(100vh - 100px); /* 确保整个测试容器在视口内 */
    display: flex;
    flex-direction: column;
}

/* 顶部信息栏 */
.test-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    padding: 10px 20px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    flex-shrink: 0; /* 不压缩 */
}

.test-info {
    display: flex;
    gap: 20px;
    font-size: 16px;
    font-weight: 500;
}

.group-info {
    color: #909399;
}

.test-timer {
    font-size: 20px;
    font-weight: bold;
    color: #409EFF;
    padding: 8px 16px;
    background: #ecf5ff;
    border-radius: 4px;
}

.timer-warning {
    color: #F56C6C;
    background: #fef0f0;
    animation: pulse 1s infinite;
}

@keyframes pulse {
    0%, 100% {
        opacity: 1;
    }
    50% {
        opacity: 0.6;
    }
}

/* 题目区域 */
.question-area {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
    margin-bottom: 15px;
    height: calc(100vh - 200px); /* 固定高度，确保不超出视口 */
    display: flex;
    flex-direction: column;
}

/* 主图片 */
.main-image-container {
    text-align: center;
    margin-bottom: 15px;
    padding: 15px;
    background: #fafafa;
    border-radius: 4px;
    flex: 1; /* 占用剩余空间 */
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 0; /* 允许flex收缩 */
}

.main-image {
    max-width: 100%;
    max-height: 100%; /* 使用100%以适应容器 */
    object-fit: contain;
}

/* 选项区域 */
.options-container {
    max-width: 900px;
    margin-left: auto;
    margin-right: auto;
    flex-shrink: 0; /* 不压缩选项区域 */
}

.options-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
}

.options-grid.options-8 {
    grid-template-columns: repeat(4, 1fr);
}

.option-item {
    position: relative;
    cursor: pointer;
    border: 3px solid #dcdfe6;
    border-radius: 6px;
    padding: 6px;
    background: #fafafa;
    transition: all 0.3s;
    aspect-ratio: 1; /* 保持正方形 */
}

.option-item:hover {
    border-color: #409EFF;
    transform: translateY(-4px);
    box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.option-item.selected {
    border-color: #409EFF;
    background: #ecf5ff;
    box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
}

.option-image {
    width: 100%;
    height: 100%;
    object-fit: contain;
    display: block;
}

/* 隐藏选项标签以节省空间 */
.option-label {
    display: none;
}

/* 导航按钮 */
.navigation-buttons {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-top: 10px;
}

/* 侧边栏 */
.sidebar {
    position: fixed;
    left: 0;
    top: 60px;
    height: calc(100vh - 60px);
    width: 280px;
    background: white;
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
    transition: transform 0.3s;
    z-index: 100;
}

.sidebar.collapsed {
    transform: translateX(-280px); /* 隐藏到左侧 */
}

.sidebar-toggle {
    position: absolute;
    right: -40px;
    top: 50%;
    transform: translateY(-50%);
    z-index: 101;
}

.sidebar-content {
    height: 100%;
    overflow-y: auto;
    padding: 20px;
}

.sidebar-content h3 {
    margin-bottom: 20px;
    color: #409EFF;
    text-align: center;
}

.group-panel {
    margin-bottom: 20px;
}

.group-header {
    font-weight: bold;
    margin-bottom: 10px;
    color: #606266;
}

.questions-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 8px;
}

.question-cell {
    aspect-ratio: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px solid #dcdfe6;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.2s;
}

.question-cell:hover {
    border-color: #409EFF;
    background: #ecf5ff;
}

.question-cell.answered {
    background: #67C23A;
    color: white;
    border-color: #67C23A;
}

.question-cell.current {
    border-color: #409EFF;
    border-width: 3px;
    background: #409EFF;
    color: white;
}

/* 结果页面 */
.result-container {
    max-width: 600px;
    margin: 0 auto;
    text-align: center;
    padding: 40px 20px;
}

.result-container h2 {
    color: #409EFF;
    margin-bottom: 30px;
    font-size: 28px;
}

.result-card {
    margin-bottom: 30px;
}

.result-item {
    display: flex;
    justify-content: space-between;
    padding: 15px 0;
    border-bottom: 1px solid #ebeef5;
}

.result-item:last-child {
    border-bottom: none;
}

.result-label {
    font-weight: bold;
    color: #606266;
    font-size: 16px;
}

.result-value {
    color: #303133;
    font-weight: bold;
    font-size: 16px;
}

.result-value.highlight {
    color: #409EFF;
    font-size: 24px;
}

.total-score {
    background-color: #f0f9eb;
    padding: 15px;
    border-radius: 4px;
    margin: 10px 0;
}

.total-score .result-value {
    color: #67C23A;
    font-size: 20px;
}

.action-buttons {
    display: flex;
    justify-content: center;
    gap: 20px;
}

/* 响应式设计 */
@media (max-width: 768px) {
    .options-grid {
        grid-template-columns: repeat(2, 1fr);
    }

    .options-grid.options-8 {
        grid-template-columns: repeat(2, 1fr);
    }

    .sidebar {
        width: 200px;
    }

    .questions-grid {
        grid-template-columns: repeat(4, 1fr);
    }
}
</style>
