<template>
    <div class="cover-page">
        <!-- 顶部品牌条 -->
        <header class="cover-topbar">
            <div class="brand">
                <span class="brand-mark">
                    <svg viewBox="0 0 32 32" aria-hidden="true">
                        <rect x="2" y="2" width="28" height="28" rx="9" fill="url(#bm)" />
                        <path d="M10 21V13.5c0-1.7 1.4-3 3.1-3 1.3 0 2.4.8 2.9 2 .5-1.2 1.6-2 2.9-2 1.7 0 3.1 1.3 3.1 3V21"
                              fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" />
                        <circle cx="16" cy="24.5" r="1.7" fill="#fff" />
                        <defs>
                            <linearGradient id="bm" x1="0" y1="0" x2="1" y2="1">
                                <stop offset="0%" stop-color="#7d95ff" />
                                <stop offset="100%" stop-color="#3a56d4" />
                            </linearGradient>
                        </defs>
                    </svg>
                </span>
                <span class="brand-name">中小学生学习困难筛查线上平台</span>
            </div>
        </header>

        <main class="cover-main">
            <!-- 左：主视觉 -->
            <section class="cover-hero">
                <h1 class="hero-title">中小学生学习困难筛查线上平台</h1>
                <div class="hero-art">
                    <HeroIllustration />
                </div>
                <ul class="module-chips">
                    <li><i class="dot dot-reading"></i>阅读流畅性测试</li>
                    <li><i class="dot dot-oral"></i>朗读流畅性测试</li>
                    <li><i class="dot dot-attention"></i>注意力筛查测试</li>
                    <li><i class="dot dot-calc"></i>计算流畅性测试</li>
                    <li><i class="dot dot-literacy"></i>识字量测验</li>
                    <li><i class="dot dot-raven"></i>图形推理测试</li>
                </ul>
            </section>

            <!-- 右：信息填写 -->
            <section class="cover-form">
                <div class="form-card">
                    <div class="form-head">
                        <span class="sec-eyebrow">STEP 1</span>
                        <h2>请填写您的基本信息</h2>
                    </div>

                    <el-form ref="formRef" :model="userForm" :rules="rules" label-position="top" class="info-form">
                        <div class="form-row">
                            <el-form-item label="姓名" prop="name">
                                <el-input v-model="userForm.name" placeholder="请输入你的姓名" size="large"></el-input>
                            </el-form-item>

                            <el-form-item label="出生日期" prop="birth_date">
                                <el-date-picker v-model="userForm.birth_date" type="date" placeholder="请选择出生日期"
                                    class="full-width" size="large" format="YYYY-MM-DD" value-format="YYYY-MM-DD"></el-date-picker>
                            </el-form-item>
                        </div>

                        <el-form-item label="学校" prop="school">
                            <el-autocomplete v-model="userForm.school" :fetch-suggestions="querySchools" placeholder="请输入或选择学校"
                                class="full-width" size="large"></el-autocomplete>
                        </el-form-item>

                        <div class="form-row">
                            <el-form-item label="年级" prop="grade">
                                <el-input-number v-model="userForm.grade" :min="1" :max="12" placeholder="请输入年级"
                                    class="full-width" size="large" controls-position="right"></el-input-number>
                            </el-form-item>

                            <el-form-item label="班级" prop="class_number">
                                <el-input-number v-model="userForm.class_number" :min="1" :max="30" placeholder="请输入班级"
                                    class="full-width" size="large" controls-position="right"></el-input-number>
                            </el-form-item>
                        </div>

                        <el-form-item class="submit-item">
                            <el-button type="primary" size="large" @click="submitForm" class="submit-btn">开始实验</el-button>
                        </el-form-item>
                    </el-form>
                </div>
            </section>
        </main>
    </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import HeroIllustration from './HeroIllustration.vue';

const router = useRouter();
const formRef = ref(null);
const recentSchools = ref([]);

const userForm = reactive({
    name: '',
    school: '',
    grade: null,
    class_number: null,
    birth_date: null
});

const rules = {
    name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
    school: [{ required: true, message: '请输入学校', trigger: 'blur' }],
    grade: [{ required: true, message: '请输入年级', trigger: 'blur' }],
    class_number: [{ required: true, message: '请输入班级', trigger: 'blur' }],
    birth_date: [{ required: true, message: '请选择出生日期', trigger: 'change' }]
};

// 获取最近的学校信息
onMounted(async () => {
    try {
        const response = await fetch('/api/users/schools/recent');
        if (response.ok) {
            const data = await response.json();
            recentSchools.value = data.schools;

            // 如果有最近的学校，自动填充最后一个
            if (recentSchools.value.length > 0) {
                userForm.school = recentSchools.value[recentSchools.value.length - 1];
            }
        }
    } catch (error) {
        console.error('获取学校信息失败:', error);
    }
});

// 提供学校自动完成功能
const querySchools = (queryString, callback) => {
    const results = queryString
        ? recentSchools.value.filter(school =>
            school.toLowerCase().includes(queryString.toLowerCase()))
        : recentSchools.value;

    callback(results.map(school => ({ value: school })));
};

// 修改 submitForm 函数
const submitForm = async () => {
    if (!formRef.value) return;

    // 后台管理入口：用户名输入 Yanglab 时直接进入管理后台（无需密码）
    if (userForm.name.trim() === 'Yanglab') {
        router.push('/yanglab');
        return;
    }

    await formRef.value.validate(async (valid) => {
        if (valid) {
            try {
                // 调用后端API创建或获取用户信息
                const response = await fetch('/api/users/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(userForm)
                });

                const result = await response.json();

                if (response.ok) {
                    // 后端直接返回用户对象，保存包含ID的完整用户信息到本地存储
                    localStorage.setItem('userInfo', JSON.stringify(result));

                    // 导航到测试选择页面
                    router.push('/selection');
                } else {
                    throw new Error(result.detail || result.message || '创建用户失败');
                }
            } catch (error) {
                console.error('创建用户失败:', error);
                ElMessage.error('创建用户失败，请重试');
            }
        }
    });
};
</script>

<style scoped>
.cover-page {
    min-height: 100vh;
    background:
        radial-gradient(1200px 620px at 8% -12%, rgba(76, 111, 255, .16), transparent 60%),
        radial-gradient(1000px 560px at 100% 10%, rgba(18, 179, 168, .14), transparent 58%),
        radial-gradient(760px 520px at 60% 108%, rgba(240, 169, 44, .12), transparent 60%),
        var(--canvas);
    display: flex;
    flex-direction: column;
}

/* 顶部品牌 */
.cover-topbar {
    padding: 22px clamp(20px, 5vw, 56px);
}

.brand {
    display: inline-flex;
    align-items: center;
    gap: 12px;
}

.brand-mark svg {
    width: 38px;
    height: 38px;
    display: block;
}

.brand-name {
    font-size: 16px;
    font-weight: 700;
    color: var(--ink-900);
    letter-spacing: .01em;
}

/* 主区域 */
.cover-main {
    flex: 1;
    display: grid;
    grid-template-columns: minmax(0, 1.05fr) minmax(380px, .95fr);
    align-items: center;
    gap: clamp(24px, 5vw, 72px);
    padding: clamp(8px, 2vw, 24px) clamp(20px, 5vw, 56px) clamp(32px, 5vw, 64px);
    max-width: 1360px;
    width: 100%;
    margin: 0 auto;
}

/* 左侧主视觉 */
.cover-hero {
    text-align: center;
}

.hero-title {
    font-size: clamp(26px, 3.4vw, 42px);
    line-height: 1.25;
    background: linear-gradient(120deg, var(--ink-900) 20%, var(--brand-600) 78%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    margin-bottom: clamp(8px, 2vw, 20px);
}

.hero-art {
    display: flex;
    justify-content: center;
}

.module-chips {
    list-style: none;
    margin: clamp(8px, 2vw, 20px) 0 0;
    padding: 0;
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 10px;
}

.module-chips li {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    border-radius: var(--r-full);
    background: rgba(255, 255, 255, .82);
    border: 1px solid var(--line);
    box-shadow: var(--sh-xs);
    color: var(--ink-700);
    font-size: 13px;
    font-weight: 600;
    backdrop-filter: blur(6px);
}

.dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
}

.dot-reading { background: var(--hue-reading); }
.dot-oral { background: var(--hue-oral); }
.dot-attention { background: var(--hue-attention); }
.dot-calc { background: var(--hue-calc); }
.dot-literacy { background: var(--hue-literacy); }
.dot-raven { background: var(--hue-raven); }

/* 右侧表单卡 */
.cover-form {
    display: flex;
    justify-content: center;
}

.form-card {
    width: 100%;
    max-width: 460px;
    background: rgba(255, 255, 255, .94);
    backdrop-filter: blur(14px);
    border: 1px solid rgba(255, 255, 255, .9);
    border-radius: var(--r-xl);
    box-shadow: var(--sh-lg);
    padding: clamp(24px, 3vw, 36px);
}

.form-head {
    margin-bottom: 22px;
}

.form-head h2 {
    margin-top: 12px;
    font-size: 22px;
}

.form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0 16px;
}

.info-form :deep(.el-form-item) {
    margin-bottom: 18px;
}

.info-form :deep(.el-form-item__label) {
    padding-bottom: 6px;
    font-size: 13px;
    color: var(--ink-500);
}

.full-width {
    width: 100%;
}

.info-form :deep(.el-input-number .el-input__inner) {
    text-align: left;
}

.submit-item {
    margin-bottom: 0 !important;
    margin-top: 6px;
}

.submit-btn {
    width: 100%;
    height: 50px;
    font-size: 17px;
    letter-spacing: .08em;
}

@media (max-width: 992px) {
    .cover-main {
        grid-template-columns: 1fr;
        gap: 28px;
    }

    .hero-art :deep(.hero-svg) {
        max-width: 400px;
    }
}

@media (max-width: 520px) {
    .form-row {
        grid-template-columns: 1fr;
    }

    .module-chips li {
        font-size: 12px;
        padding: 6px 12px;
    }
}
</style>
