<template>
    <div class="user-info-container">
        <el-card class="form-card">
            <template #header>
                <div class="card-header">
                    <h1>阅读流畅性实验</h1>
                    <p>请填写您的基本信息</p>
                </div>
            </template>

            <el-form ref="formRef" :model="userForm" :rules="rules" label-position="top">
                <el-form-item label="姓名" prop="name">
                    <el-input v-model="userForm.name" placeholder="请输入你的姓名"></el-input>
                </el-form-item>

                <el-form-item label="学校" prop="school">
                    <el-autocomplete v-model="userForm.school" :fetch-suggestions="querySchools" placeholder="请输入或选择学校"
                        class="full-width"></el-autocomplete>
                </el-form-item>

                <el-form-item label="年级" prop="grade">
                    <el-input-number v-model="userForm.grade" :min="1" :max="12" placeholder="请输入年级"
                        class="full-width"></el-input-number>
                </el-form-item>

                <el-form-item label="班级" prop="classNumber">
                    <el-input-number v-model="userForm.classNumber" :min="1" :max="30" placeholder="请输入班级"
                        class="full-width"></el-input-number>
                </el-form-item>

                <el-form-item>
                    <el-button type="primary" @click="submitForm" class="submit-btn">开始实验</el-button>
                </el-form-item>
            </el-form>
        </el-card>
    </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const formRef = ref(null);
const recentSchools = ref([]);

const userForm = reactive({
    name: '',
    school: '',
    grade: null,
    classNumber: null
});

const rules = {
    name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
    school: [{ required: true, message: '请输入学校', trigger: 'blur' }],
    grade: [{ required: true, message: '请输入年级', trigger: 'blur' }],
    classNumber: [{ required: true, message: '请输入班级', trigger: 'blur' }]
};

// 获取最近的学校信息
onMounted(async () => {
    try {
        const response = await fetch('/api/users/schools/recent');
        if (response.ok) {
            const data = await response.json();
            recentSchools.value = data.schools;

            // 如果有最近的学校，自动填充第一个
            if (recentSchools.value.length > 0) {
                userForm.school = recentSchools.value[0];
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

// 提交表单
const submitForm = async () => {
    if (!formRef.value) return;

    await formRef.value.validate(async (valid) => {
        if (valid) {
            // 保存用户信息到本地存储
            localStorage.setItem('userInfo', JSON.stringify(userForm));

            // 导航到实验页面
            router.push('/experiment');
        }
    });
};
</script>

<style scoped>
.user-info-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    padding: 20px;
}

.form-card {
    width: 100%;
    max-width: 500px;
}

.card-header {
    text-align: center;
}

.full-width {
    width: 100%;
}

.submit-btn {
    width: 100%;
    margin-top: 20px;
}

h1 {
    font-size: 24px;
    color: #409EFF;
    margin-bottom: 10px;
}
</style>