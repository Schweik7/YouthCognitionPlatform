<template>
    <div class="experiment-container">
        <!-- 调试面板 -->
        <div v-if="debugMode" class="debug-panel">
            <h3>调试模式</h3>
            <div class="debug-controls">
                <el-input-number v-model="remainingTime" :min="0" :max="180" label="剩余时间(秒)"></el-input-number>
                <el-button type="primary" @click="updateTimer">更新时间</el-button>
                <el-button type="warning" @click="endTest">结束测试</el-button>
            </div>
        </div>

        <!-- 实验内容区域 -->
        <div class="content-area">
            <!-- 指导语阶段 -->
            <div v-if="phase === 'welcome'" class="instruction">
                <h2>注意力筛查测试</h2>
                <p>欢迎参加注意力筛查测试，这个测试将评估你的注意力集中和判断能力。</p>
                <p>在测试中，你将看到一系列符号，需要找出并点击所有的目标符号。</p>
                <p>请认真完成测试，尽可能快速准确地找出所有目标符号。</p>
                <el-button type="primary" class="continue-btn" @click="nextPhase">下一步</el-button>
            </div>

            <!-- 练习阶段说明 -->
            <div v-else-if="phase === 'practice-intro'" class="instruction">
                <h2>练习阶段</h2>
                <p>这里有许多符号，请仔细地一个一个地看。</p>
                <p>你需要找出并点击所有的<span class="target-symbol">{{ targetSymbol }}</span>符号。</p>
                <p>请先完成一个练习行，熟悉测试流程。</p>
                <el-button type="primary" class="continue-btn" @click="startPractice">开始练习</el-button>
            </div>

            <!-- 练习阶段 -->
            <div v-else-if="phase === 'practice'" class="symbol-container">
                <div class="instruction-bar">
                    <p>请点击所有的<span class="target-symbol">{{ targetSymbol }}</span>符号。</p>
                    <p v-if="targetRemaining > 0" class="remaining-targets">还有 {{ targetRemaining }} 个目标符号未找到</p>
                    <p v-else class="remaining-targets success">已找到所有目标符号！</p>
                </div>

                <div class="symbol-grid">
                    <div v-for="(symbol, index) in currentRow" :key="index" class="symbol-cell"
                        :class="{ 'clicked': symbol.is_clicked }" @click="handleSymbolClick(symbol)">
                        <span class="symbol">{{ symbol.symbol }}</span>
                        <div v-if="symbol.is_clicked" class="circle-animation"></div>
                    </div>
                </div>

                <div class="action-buttons">
                    <el-button type="primary" :disabled="targetRemaining > 0" @click="nextPhase">
                        继续
                    </el-button>
                </div>
            </div>

            <!-- 正式阶段说明 -->
            <div v-else-if="phase === 'formal-intro'" class="instruction">
                <h2>正式测试</h2>
                <p>好的，练习已完成。现在开始正式测试。</p>
                <p>在接下来的测试中，你将看到多行符号，需要点击所有的<span class="target-symbol">{{ targetSymbol }}</span>符号。</p>
                <p>测试总时间为3分钟。如果你提前完成，可以点击提交按钮结束测试。</p>
                <p>准备好后，点击"开始"按钮，计时将立即开始！</p>
                <el-button type="primary" class="continue-btn" @click="startFormalTest">开始</el-button>
            </div>

            <!-- 正式阶段测试 -->
            <div v-else-if="phase === 'formal' && !testEnded" class="symbol-container formal-test">
                <div class="test-header">
                    <div class="test-info">
                        <p>点击所有的<span class="target-symbol">{{ targetSymbol }}</span>符号</p>
                        <p>当前行: {{ currentRowIndex + 1 }}/{{ totalRows }}</p>
                    </div>
                    <div class="test-timer">
                        <span>{{ formatTime(remainingTime) }}</span>
                    </div>
                </div>

                <div class="symbol-grid">
                    <div v-for="(symbol, index) in currentRow" :key="index" class="symbol-cell"
                        :class="{ 'clicked': symbol.is_clicked }" @click="handleSymbolClick(symbol)">
                        <span class="symbol">{{ symbol.symbol }}</span>
                        <div v-if="symbol.is_clicked" class="circle-animation"></div>
                    </div>
                </div>

                <div class="action-buttons">
                    <el-button type="primary" @click="nextRow">下一行</el-button>
                    <el-button type="success" @click="submitTest">提交测试</el-button>
                </div>

                <!-- 计时器沙漏 -->
                <div class="timer-container">
                    <div class="hourglass-container">
                        <div class="hourglass">
                            <div class="hourglass-top" :style="hourglassTopStyle"></div>
                            <div class="hourglass-bottom" :style="hourglassBottomStyle"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 测试结果 -->
            <div v-else-if="phase === 'result'" class="result-container">
                <h2>测试结果</h2>

                <el-card class="result-card">
                    <div class="result-item">
                        <div class="result-label">正确点击数:</div>
                        <div class="result-value">{{ testResults.correctCount }}</div>
                    </div>
                    <div class="result-item">
                        <div class="result-label">错误点击数:</div>
                        <div class="result-value">{{ testResults.incorrectCount }}</div>
                    </div>
                    <div class="result-item">
                        <div class="result-label">遗漏数量:</div>
                        <div class="result-value">{{ testResults.missedCount }}</div>
                    </div>
                    <div class="result-item total-score">
                        <div class="result-label">总分:</div>
                        <div class="result-value">{{ testResults.totalScore.toFixed(1) }}</div>
                    </div>
                    <div class="result-item">
                        <div class="result-label">用时:</div>
                        <div class="result-value">{{ formatTime(testResults.totalTime) }}</div>
                    </div>
                    <div class="result-item">
                        <div class="result-label">准确率:</div>
                        <div class="result-value">{{ testResults.accuracy.toFixed(1) }}%</div>
                    </div>
                </el-card>

                <div class="action-buttons">
                    <el-button type="primary" @click="goToSelection">返回测试选择</el-button>
                    <el-button @click="restartTest">重新测试</el-button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';

const router = useRouter();

// 状态变量
const phase = ref('welcome'); // 实验阶段: welcome, practice-intro, practice, formal-intro, formal, result
const targetSymbol = ref('Ψ'); // 目标符号
const userId = ref(null);
const testSessionId = ref(null);
const practiceSequence = ref([]); // 练习阶段序列
const formalSequence = ref([]); // 正式阶段序列
const currentRowIndex = ref(0); // 当前行索引
const totalRows = ref(16); // 总行数
const targetRemaining = ref(0); // 剩余目标符号数量
const debugMode = ref(false); // 调试模式
const testEnded = ref(false); // 测试是否结束
const remainingTime = ref(180); // 3分钟倒计时
const timerInterval = ref(null); // 计时器
const testResults = ref({
    correctCount: 0,
    incorrectCount: 0,
    missedCount: 0,
    totalScore: 0,
    totalTime: 0,
    accuracy: 0
});

// 沙漏样式计算
const hourglassTopStyle = computed(() => {
    const percentage = (remainingTime.value / 180) * 100;
    return {
        height: `${percentage / 2}%`,
        transition: 'height 1s linear'
    };
});

const hourglassBottomStyle = computed(() => {
    const percentage = 100 - (remainingTime.value / 180) * 100;
    return {
        height: `${percentage / 2}%`,
        backgroundColor: percentage > 80 ? '#409EFF' : '#E6E6E6',
        transition: 'height 1s linear, background-color 1s linear'
    };
});

// 当前行的符号
const currentRow = computed(() => {
    if (phase.value === 'practice') {
        // 练习阶段只有一行
        return practiceSequence.value;
    } else if (phase.value === 'formal') {
        // 正式阶段，根据当前行索引获取
        const startIdx = currentRowIndex.value * 25;
        const endIdx = startIdx + 25;
        return formalSequence.value.slice(startIdx, endIdx);
    }
    return [];
});

// 格式化时间显示
const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
};

// 更新计时器
const updateTimer = () => {
    if (phase.value !== 'formal' || testEnded.value) return;

    remainingTime.value--;

    if (remainingTime.value <= 0) {
        clearInterval(timerInterval.value);
        endTest();
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

        // 如果已经有userId字段，直接使用
        if (userInfo.userId) {
            userId.value = userInfo.userId;
            console.log('已存在的用户ID:', userId.value);
            return;
        }

        // 否则，尝试查找或创建用户
        const response = await fetch('/api/users/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: userInfo.name,
                school: userInfo.school,
                grade: userInfo.grade,
                class_number: userInfo.classNumber || userInfo.class_number
            })
        });

        if (response.ok) {
            const data = await response.json();
            userId.value = data.id;
            console.log('新用户创建成功，ID:', userId.value);

            // 更新localStorage中的用户信息
            const updatedUserInfo = { ...userInfo, userId: data.id };
            localStorage.setItem('userInfo', JSON.stringify(updatedUserInfo));
        } else {
            console.error('创建用户失败:', await response.text());
        }
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
        const response = await fetch('/api/attention-test/sessions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId.value,
                target_symbol: targetSymbol.value
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

// 获取练习序列
const fetchPracticeSequence = async () => {
    try {
        const response = await fetch(`/api/attention-test/practice-sequence?target_symbol=${targetSymbol.value}`);
        if (response.ok) {
            const data = await response.json();
            practiceSequence.value = data;

            // 计算目标符号数量
            targetRemaining.value = data.filter(item => item.is_target).length;
        } else {
            ElMessage.error('获取练习序列失败');
        }
    } catch (error) {
        console.error('获取练习序列失败:', error);
        ElMessage.error('网络错误，无法获取练习序列');
    }
};

// 获取正式测试序列
const fetchFormalSequence = async () => {
    try {
        const response = await fetch(`/api/attention-test/test-sequence?target_symbol=${targetSymbol.value}`);
        if (response.ok) {
            const data = await response.json();
            formalSequence.value = data;
            totalRows.value = Math.ceil(data.length / 25);
        } else {
            ElMessage.error('获取测试序列失败');
        }
    } catch (error) {
        console.error('获取测试序列失败:', error);
        ElMessage.error('网络错误，无法获取测试序列');
    }
};

// 处理符号点击
const handleSymbolClick = (symbol) => {
    if (symbol.is_clicked) return; // 已点击过的不再处理

    // 标记为已点击
    symbol.is_clicked = true;

    // 更新剩余目标符号数量（仅在练习阶段）
    if (phase.value === 'practice' && symbol.is_target) {
        targetRemaining.value--;
    }

    // 如果是正式阶段，保存点击记录
    if (phase.value === 'formal' && testSessionId.value) {
        saveSymbolClick(symbol);
    }
};

// 保存符号点击记录
const saveSymbolClick = async (symbol) => {
    if (!testSessionId.value || !userId.value) return;

    try {
        const response = await fetch('/api/attention-test/records', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId.value,
                test_session_id: testSessionId.value,
                row_index: symbol.row_index,
                col_index: symbol.col_index,
                symbol: symbol.symbol,
                is_target: symbol.is_target,
                is_clicked: true
            })
        });

        if (!response.ok) {
            console.error('保存点击记录失败:', await response.text());
        }
    } catch (error) {
        console.error('保存点击记录请求失败:', error);
    }
};

// 进入下一阶段
const nextPhase = () => {
    switch (phase.value) {
        case 'welcome':
            phase.value = 'practice-intro';
            break;
        case 'practice':
            phase.value = 'formal-intro';
            break;
        case 'formal-intro':
            startFormalTest();
            break;
        default:
            break;
    }
};

// 开始练习阶段
const startPractice = async () => {
    await fetchPracticeSequence();
    phase.value = 'practice';
};

// 开始正式测试
const startFormalTest = async () => {
    // 获取用户信息
    await getUserInfo();

    // 创建测试会话
    await createTestSession();

    // 获取测试序列
    await fetchFormalSequence();

    // 准备测试
    currentRowIndex.value = 0;
    remainingTime.value = 180;
    testEnded.value = false;
    phase.value = 'formal';

    // 启动计时器
    startTimer();
};

// 进入下一行
const nextRow = async () => {
    // 保存当前行中未点击的符号记录
    if (testSessionId.value && userId.value) {
        for (const symbol of currentRow.value) {
            if (!symbol.is_clicked) {
                try {
                    await fetch('/api/attention-test/records', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            user_id: userId.value,
                            test_session_id: testSessionId.value,
                            row_index: symbol.row_index,
                            col_index: symbol.col_index,
                            symbol: symbol.symbol,
                            is_target: symbol.is_target,
                            is_clicked: false
                        })
                    });
                } catch (error) {
                    console.error('保存未点击记录失败:', error);
                }
            }
        }
    }

    // 判断是否已到最后一行
    if (currentRowIndex.value < totalRows.value - 1) {
        currentRowIndex.value++;
    } else {
        // 已完成所有行，询问是否结束测试
        ElMessageBox.confirm(
            '已到达最后一行，是否结束测试？',
            '测试完成',
            {
                confirmButtonText: '结束测试',
                cancelButtonText: '返回查看',
                type: 'info',
            }
        )
            .then(() => {
                endTest();
            })
            .catch(() => {
                // 用户取消，返回到最后一行
            });
    }
};

// 提交测试
const submitTest = () => {
    ElMessageBox.confirm(
        '确定要提交测试吗？',
        '提交确认',
        {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning',
        }
    )
        .then(() => {
            endTest();
        })
        .catch(() => {
            // 用户取消提交
        });
};

// 结束测试
const endTest = async () => {
    if (testEnded.value) return;

    testEnded.value = true;
    clearInterval(timerInterval.value);

    // 完成测试会话并获取结果
    try {
        const response = await fetch(`/api/attention-test/sessions/${testSessionId.value}/complete`, {
            method: 'POST'
        });

        if (response.ok) {
            const resultsResponse = await fetch(`/api/attention-test/sessions/${testSessionId.value}/results`);

            if (resultsResponse.ok) {
                const data = await resultsResponse.json();

                // 设置测试结果
                testResults.value = {
                    correctCount: data.stats.correctCount,
                    incorrectCount: data.stats.incorrectCount,
                    missedCount: data.stats.missedCount,
                    totalScore: data.stats.totalScore,
                    totalTime: data.stats.totalTimeSeconds || (180 - remainingTime.value),
                    accuracy: data.stats.accuracy
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
        console.error('结束测试请求失败:', error);
        ElMessage.error('网络错误，无法结束测试');
    }
};

// 返回测试选择
const goToSelection = () => {
    router.push('/selection');
};

// 重新测试
const restartTest = () => {
    // 重置状态
    phase.value = 'practice-intro';
    testSessionId.value = null;
    currentRowIndex.value = 0;
    testEnded.value = false;
    remainingTime.value = 180;
    practiceSequence.value = [];
    formalSequence.value = [];
};

// 键盘监听函数
const keyHandler = (e) => {
    // 检测是否同时按下【】键 (Alt+[ 和 Alt+])
    if ((e.key === '[' && e.altKey) || (e.key === ']' && e.altKey)) {
        debugMode.value = !debugMode.value;
        return;
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

// 观察remainingTime变化，以便在调试模式下更新
watch(remainingTime, (newVal) => {
    if (debugMode.value && phase.value === 'formal') {
        // 调试模式下手动更新倒计时，触发计算属性重新计算沙漏样式
    }
});
</script>

<style scoped>
/* 全局样式 */
.experiment-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    min-height: 100vh;
    padding: 20px;
}

.content-area {
    width: 100%;
    max-width: 900px;
    margin: 0 auto;
    padding: 20px;
    box-sizing: border-box;
}

/* 调试面板 */
.debug-panel {
    position: fixed;
    top: 0;
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

.target-symbol {
    font-size: 1.2em;
    font-weight: bold;
    color: #409EFF;
    padding: 0 5px;
}

.continue-btn {
    margin: 20px auto;
    display: block;
    min-width: 120px;
    font-weight: bold;
}

/* 符号网格样式 */
.symbol-container {
    max-width: 900px;
    margin: 0 auto;
    padding: 20px;
}

.instruction-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    flex-wrap: wrap;
}

.remaining-targets {
    background-color: #f0f9eb;
    color: #67C23A;
    padding: 5px 10px;
    border-radius: 4px;
    font-weight: bold;
}

.remaining-targets.success {
    background-color: #67C23A;
    color: white;
}

.symbol-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 10px;
    margin-bottom: 20px;
}

@media (min-width: 768px) {
    .symbol-grid {
        grid-template-columns: repeat(10, 1fr);
    }
}

@media (min-width: 1024px) {
    .symbol-grid {
        grid-template-columns: repeat(25, 1fr);
    }
}

.symbol-cell {
    position: relative;
    height: 40px;
    display: flex;
    justify-content: center;
    align-items: center;
    background-color: #f5f7fa;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.3s;
    overflow: hidden;
}

.symbol-cell:hover {
    background-color: #ecf5ff;
    transform: translateY(-2px);
}

.symbol-cell.clicked {
    background-color: #ecf5ff;
    border: 1px solid #409EFF;
    color: #409EFF;
}

.symbol {
    font-size: 18px;
    font-weight: bold;
}

/* 圈出效果动画 */
.circle-animation {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    border-radius: 50%;
    border: 2px solid #409EFF;
    animation: draw-circle 0.5s ease forwards;
}

@keyframes draw-circle {
    0% {
        clip-path: circle(0% at center);
        opacity: 0;
    }

    100% {
        clip-path: circle(100% at center);
        opacity: 1;
    }
}

/* 按钮容器 */
.action-buttons {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-top: 20px;
}

/* 正式测试阶段样式 */
.test-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.test-info {
    display: flex;
    flex-direction: column;
    gap: 5px;
}

.test-timer {
    font-size: 1.5em;
    font-weight: bold;
    color: #409EFF;
    background-color: white;
    padding: 5px 10px;
    border-radius: 4px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

/* 计时器和沙漏 */
.timer-container {
    position: fixed;
    top: 20px;
    right: 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.hourglass-container {
    margin-top: 10px;
    display: flex;
    justify-content: center;
}

.hourglass {
    position: relative;
    width: 30px;
    height: 50px;
}

.hourglass-top {
    position: absolute;
    top: 0;
    width: 30px;
    height: 25px;
    background-color: #409EFF;
    clip-path: polygon(0 0, 100% 0, 50% 100%, 0 0);
}

.hourglass-bottom {
    position: absolute;
    bottom: 0;
    width: 30px;
    height: 0px;
    background-color: #E6E6E6;
    clip-path: polygon(0 100%, 100% 100%, 50% 0, 0 100%);
}

/* 结果页面样式 */
.result-container {
    max-width: 600px;
    margin: 0 auto;
    text-align: center;
}

.result-container h2 {
    color: #409EFF;
    margin-bottom: 20px;
}

.result-card {
    margin-bottom: 30px;
}

.result-item {
    display: flex;
    justify-content: space-between;
    padding: 10px 0;
    border-bottom: 1px solid #ebeef5;
}

.result-item:last-child {
    border-bottom: none;
}

.result-label {
    font-weight: bold;
    color: #606266;
}

.result-value {
    color: #303133;
    font-weight: bold;
}


.total-score {
    font-size: 1.2em;
    background-color: #f0f9eb;
    padding: 10px;
    border-radius: 4px;
    margin: 10px 0;
}

.total-score .result-value {
    color: #67C23A;
    font-size: 1.2em;
}
</style>