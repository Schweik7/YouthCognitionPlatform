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
            <div class="topbar-actions">
                <el-button class="admin-entry" plain @click="adminDialog = true">后台登录</el-button>
            </div>
        </header>

        <main class="cover-main">
            <!-- 左：主视觉 -->
            <section class="cover-hero">
                <div class="hero-art">
                    <HeroIllustration />
                </div>
            </section>

            <!-- 右：账号登录 / 注册 -->
            <section class="cover-form">
                <div class="form-card">
                    <div class="auth-switch">
                        <button type="button" :class="['switch-btn', { active: mode === 'login' }]"
                            @click="mode = 'login'">快速登录</button>
                        <button type="button" :class="['switch-btn', { active: mode === 'register' }]"
                            @click="mode = 'register'">首次登记</button>
                    </div>

                    <!-- 登录 -->
                    <el-form v-if="mode === 'login'" ref="loginRef" :model="loginForm" :rules="loginRules"
                        label-position="top" class="info-form" @submit.prevent>
                        <div class="form-row">
                            <el-form-item label="学号" prop="student_id">
                                <el-input v-model="loginForm.student_id" placeholder="请输入学号" size="large"
                                    @keyup.enter="submitLogin"></el-input>
                            </el-form-item>

                            <el-form-item label="姓名" prop="name">
                                <el-input v-model="loginForm.name" placeholder="请输入姓名" size="large"
                                    @keyup.enter="submitLogin"></el-input>
                            </el-form-item>
                        </div>

                        <el-form-item label="测验序号" prop="test_round">
                            <el-input-number v-model="loginForm.test_round" :min="1" :max="20" placeholder="本次是第几次测验"
                                class="full-width" size="large" controls-position="right"></el-input-number>
                        </el-form-item>

                        <el-form-item class="submit-item">
                            <el-button type="primary" size="large" class="submit-btn" :loading="loading"
                                @click="submitLogin">进入测评</el-button>
                        </el-form-item>

                        <p class="form-tip">第一次使用？<a href="javascript:void(0)" @click="mode = 'register'">先去登记</a></p>
                    </el-form>

                    <!-- 注册 -->
                    <el-form v-else ref="registerRef" :model="registerForm" :rules="registerRules" label-position="top"
                        class="info-form" @submit.prevent>
                        <div class="form-row">
                            <el-form-item label="学号" prop="student_id">
                                <el-input v-model="registerForm.student_id" placeholder="请输入学号"
                                    size="large"></el-input>
                            </el-form-item>

                            <el-form-item label="姓名" prop="name">
                                <el-input v-model="registerForm.name" placeholder="请输入你的姓名" size="large"></el-input>
                            </el-form-item>
                        </div>

                        <el-form-item label="出生日期" prop="birth_date">
                            <el-date-picker v-model="registerForm.birth_date" type="date" placeholder="请选择出生日期"
                                class="full-width" size="large" format="YYYY-MM-DD"
                                value-format="YYYY-MM-DD"></el-date-picker>
                        </el-form-item>

                        <el-form-item label="学校" prop="school">
                            <el-autocomplete v-model="registerForm.school" :fetch-suggestions="querySchools"
                                placeholder="请输入或选择学校" class="full-width" size="large"></el-autocomplete>
                        </el-form-item>

                        <div class="form-row">
                            <el-form-item label="年级" prop="grade">
                                <el-input-number v-model="registerForm.grade" :min="1" :max="12" placeholder="请输入年级"
                                    class="full-width" size="large" controls-position="right"></el-input-number>
                            </el-form-item>

                            <el-form-item label="班级" prop="class_number">
                                <el-input-number v-model="registerForm.class_number" :min="1" :max="30"
                                    placeholder="请输入班级" class="full-width" size="large"
                                    controls-position="right"></el-input-number>
                            </el-form-item>
                        </div>

                        <el-form-item class="submit-item">
                            <el-button type="primary" size="large" class="submit-btn" :loading="loading"
                                @click="submitRegister">登记并开始</el-button>
                        </el-form-item>

                        <p class="form-tip">已经登记过？<a href="javascript:void(0)" @click="mode = 'login'">快速登录</a></p>
                    </el-form>
                </div>
            </section>
        </main>

        <!-- 管理员登录 -->
        <el-dialog v-model="adminDialog" title="后台管理登录" width="380px" align-center>
            <el-form ref="adminRef" :model="adminForm" :rules="adminRules" label-position="top" @submit.prevent>
                <el-form-item label="管理员账号" prop="username">
                    <el-input v-model="adminForm.username" placeholder="请输入管理员账号" size="large"></el-input>
                </el-form-item>
                <el-form-item label="密码" prop="password">
                    <el-input v-model="adminForm.password" type="password" show-password placeholder="请输入密码"
                        size="large" @keyup.enter="submitAdminLogin"></el-input>
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="adminDialog = false">取消</el-button>
                <el-button type="primary" :loading="adminLoading" @click="submitAdminLogin">登录后台</el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import HeroIllustration from './HeroIllustration.vue';

const router = useRouter();
const mode = ref('login');
const loading = ref(false);
const loginRef = ref(null);
const registerRef = ref(null);
const recentSchools = ref([]);

const loginForm = reactive({
    student_id: '',
    name: '',
    test_round: 1
});

const registerForm = reactive({
    student_id: '',
    name: '',
    school: '',
    grade: null,
    class_number: null,
    birth_date: null
});

const adminDialog = ref(false);
const adminLoading = ref(false);
const adminRef = ref(null);
const adminForm = reactive({ username: '', password: '' });

const adminRules = {
    username: [{ required: true, message: '请输入管理员账号', trigger: 'blur' }],
    password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
};

const loginRules = {
    student_id: [{ required: true, message: '请输入学号', trigger: 'blur' }],
    name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
    test_round: [{ required: true, message: '请填写本次是第几次测验', trigger: 'blur' }]
};

const registerRules = {
    student_id: [{ required: true, message: '请输入学号', trigger: 'blur' }],
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
                registerForm.school = recentSchools.value[recentSchools.value.length - 1];
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

// 登录成功后统一保存用户信息并跳转
const enterPlatform = (user) => {
    localStorage.setItem('userInfo', JSON.stringify(user));
    localStorage.removeItem('userAvatarData');
    router.push('/selection');
};

// 管理员登录：拿到令牌后存入本地，再进入后台
const submitAdminLogin = async () => {
    if (!adminRef.value) return;

    await adminRef.value.validate(async (valid) => {
        if (!valid) return;

        adminLoading.value = true;
        try {
            const response = await fetch('/api/admin/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: adminForm.username.trim(),
                    password: adminForm.password
                })
            });
            const result = await response.json();

            if (response.ok) {
                localStorage.setItem('adminToken', result.token);
                localStorage.setItem('adminName', result.username);
                adminDialog.value = false;
                adminForm.password = '';
                router.push('/yanglab');
            } else {
                ElMessage.error(result.detail || '登录失败，请重试');
            }
        } catch (error) {
            console.error('管理员登录失败:', error);
            ElMessage.error('登录失败，请检查网络后重试');
        } finally {
            adminLoading.value = false;
        }
    });
};

const submitLogin = async () => {
    if (!loginRef.value) return;

    await loginRef.value.validate(async (valid) => {
        if (!valid) return;

        loading.value = true;
        try {
            const response = await fetch('/api/users/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    student_id: loginForm.student_id.trim(),
                    name: loginForm.name.trim(),
                    test_round: loginForm.test_round
                })
            });

            const result = await response.json();

            if (response.ok) {
                enterPlatform(result);
            } else {
                ElMessage.error(result.detail || '登录失败，请重试');
            }
        } catch (error) {
            console.error('登录失败:', error);
            ElMessage.error('登录失败，请检查网络后重试');
        } finally {
            loading.value = false;
        }
    });
};

const submitRegister = async () => {
    if (!registerRef.value) return;

    await registerRef.value.validate(async (valid) => {
        if (!valid) return;

        loading.value = true;
        try {
            const response = await fetch('/api/users/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    student_id: registerForm.student_id.trim(),
                    name: registerForm.name,
                    school: registerForm.school,
                    grade: registerForm.grade,
                    class_number: registerForm.class_number,
                    birth_date: registerForm.birth_date
                })
            });

            const result = await response.json();

            if (response.ok) {
                ElMessage.success('登记成功');
                enterPlatform(result);
            } else {
                ElMessage.error(result.detail || '登记失败，请重试');
            }
        } catch (error) {
            console.error('登记失败:', error);
            ElMessage.error('登记失败，请检查网络后重试');
        } finally {
            loading.value = false;
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
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
}

.topbar-actions {
    flex: none;
}

.admin-entry {
    border-radius: 999px;
    padding: 0 18px;
    height: 38px;
    font-weight: 600;
}

.brand {
    display: inline-flex;
    align-items: center;
    gap: 14px;
}

.brand-mark svg {
    width: 46px;
    height: 46px;
    display: block;
}

.brand-name {
    font-size: clamp(20px, 2.1vw, 30px);
    font-weight: 800;
    color: var(--ink-900);
    letter-spacing: .01em;
    white-space: nowrap;
}

/* 主区域 */
.cover-main {
    flex: 1;
    display: grid;
    grid-template-columns: minmax(0, 1.1fr) minmax(360px, 440px);
    align-items: center;
    justify-content: center;
    gap: clamp(24px, 5vw, 72px);
    padding: clamp(8px, 2vw, 24px) clamp(20px, 5vw, 56px) clamp(32px, 5vw, 64px);
    max-width: 1280px;
    width: 100%;
    margin: 0 auto;
}

/* 左侧主视觉 */
.cover-hero {
    display: flex;
    justify-content: center;
}

.hero-art {
    display: flex;
    justify-content: center;
    width: 100%;
}

.hero-art :deep(.hero-svg) {
    max-width: min(560px, 100%);
}

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

/* 登录 / 注册切换 */
.auth-switch {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 4px;
    padding: 4px;
    margin-bottom: 22px;
    background: var(--brand-50, #eef2ff);
    border-radius: var(--r-full);
}

.switch-btn {
    border: none;
    background: transparent;
    padding: 10px 0;
    border-radius: var(--r-full);
    font-size: 15px;
    font-weight: 700;
    color: var(--ink-500);
    cursor: pointer;
    transition: all .2s ease;
}

.switch-btn:hover {
    color: var(--brand-600);
}

.switch-btn.active {
    background: #fff;
    color: var(--brand-600);
    box-shadow: var(--sh-xs);
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

.form-tip {
    margin: 16px 0 0;
    text-align: center;
    font-size: 13px;
    color: var(--ink-500);
}

.form-tip a {
    color: var(--brand-600);
    font-weight: 700;
    text-decoration: none;
}

.form-tip a:hover {
    text-decoration: underline;
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
    .brand-name {
        font-size: 17px;
        white-space: normal;
    }

    .form-row {
        grid-template-columns: 1fr;
    }
}
</style>