<template>
  <!-- 学习力测评主题插画：儿童青少年 · 六大认知模块 · 成长曲线 -->
  <svg
    class="hero-svg"
    viewBox="0 0 640 560"
    role="img"
    aria-label="学习力测评插画"
    xmlns="http://www.w3.org/2000/svg"
  >
    <defs>
      <linearGradient id="hi-sky" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#e9eeff" />
        <stop offset="100%" stop-color="#f4fbfa" />
      </linearGradient>
      <linearGradient id="hi-brand" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#7d95ff" />
        <stop offset="100%" stop-color="#3a56d4" />
      </linearGradient>
      <linearGradient id="hi-teal" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#4fd6c9" />
        <stop offset="100%" stop-color="#12b3a8" />
      </linearGradient>
      <linearGradient id="hi-warm" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#ffc978" />
        <stop offset="100%" stop-color="#f0a92c" />
      </linearGradient>
      <linearGradient id="hi-book" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#ffffff" />
        <stop offset="100%" stop-color="#e7ecfb" />
      </linearGradient>
      <radialGradient id="hi-glow" cx="50%" cy="50%" r="50%">
        <stop offset="0%" stop-color="#ffe6a8" stop-opacity=".95" />
        <stop offset="100%" stop-color="#ffe6a8" stop-opacity="0" />
      </radialGradient>
      <filter id="hi-soft" x="-30%" y="-30%" width="160%" height="160%">
        <feDropShadow dx="0" dy="10" stdDeviation="14" flood-color="#2c3752" flood-opacity=".12" />
      </filter>
    </defs>

    <!-- 背景色块 -->
    <ellipse cx="320" cy="300" rx="290" ry="250" fill="url(#hi-sky)" />
    <circle cx="92" cy="118" r="52" fill="#4c6fff" opacity=".08" />
    <circle cx="566" cy="150" r="36" fill="#12b3a8" opacity=".12" />
    <circle cx="556" cy="420" r="62" fill="#f0a92c" opacity=".10" />

    <!-- 学习成长曲线（柱状 + 上升折线） -->
    <g opacity=".85">
      <rect x="72" y="404" width="26" height="42" rx="9" fill="#c7d3ff" />
      <rect x="110" y="380" width="26" height="66" rx="9" fill="#a8b9ff" />
      <rect x="148" y="348" width="26" height="98" rx="9" fill="url(#hi-brand)" />
      <path d="M78 400 L122 372 L160 336 L196 300" fill="none" stroke="#12b3a8"
            stroke-width="4" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="0 0" />
      <circle cx="196" cy="300" r="7" fill="#12b3a8" />
      <circle cx="196" cy="300" r="13" fill="#12b3a8" opacity=".22" />
    </g>

    <!-- 思维光晕 + 灯泡（学习力/洞察） -->
    <circle cx="320" cy="126" r="74" fill="url(#hi-glow)" />
    <g filter="url(#hi-soft)">
      <path d="M320 84c-25 0-45 20-45 44 0 16 9 26 16 34 5 6 8 11 8 18h42c0-7 3-12 8-18 7-8 16-18 16-34 0-24-20-44-45-44z"
            fill="url(#hi-warm)" />
      <rect x="303" y="186" width="34" height="9" rx="4.5" fill="#ffffff" opacity=".9" />
      <rect x="306" y="199" width="28" height="9" rx="4.5" fill="#ffffff" opacity=".75" />
      <!-- 灯丝：脑回路 -->
      <path d="M303 146c6-10 12-10 17 0s11 10 17 0" fill="none" stroke="#ffffff"
            stroke-width="4" stroke-linecap="round" />
      <path d="M320 146v22" stroke="#ffffff" stroke-width="4" stroke-linecap="round" />
    </g>

    <!-- 儿童：头部 -->
    <g filter="url(#hi-soft)">
      <!-- 身体 -->
      <path d="M232 520c0-52 40-92 88-92s88 40 88 92z" fill="url(#hi-brand)" />
      <!-- 领口 -->
      <path d="M296 432c8 14 16 21 24 21s16-7 24-21" fill="none" stroke="#ffffff"
            stroke-width="7" stroke-linecap="round" />
      <!-- 脖子 -->
      <rect x="304" y="392" width="32" height="42" rx="16" fill="#f6c9a8" />
      <!-- 脸 -->
      <circle cx="320" cy="342" r="62" fill="#ffd7b8" />
      <!-- 头发 -->
      <path d="M258 340c0-38 28-66 62-66s62 28 62 66c0-6-10-18-24-22-16 8-52 12-76-4-14 6-24 18-24 26z"
            fill="#3b3350" />
      <!-- 眼睛（专注状态） -->
      <circle cx="298" cy="342" r="6.5" fill="#2c3752" />
      <circle cx="344" cy="342" r="6.5" fill="#2c3752" />
      <circle cx="300" cy="339" r="2.2" fill="#ffffff" />
      <circle cx="346" cy="339" r="2.2" fill="#ffffff" />
      <!-- 笑脸 -->
      <path d="M306 366c9 8 19 8 28 0" fill="none" stroke="#d98f6a"
            stroke-width="5" stroke-linecap="round" />
      <!-- 腮红 -->
      <ellipse cx="284" cy="360" rx="9" ry="6" fill="#ff9f9f" opacity=".45" />
      <ellipse cx="358" cy="360" rx="9" ry="6" fill="#ff9f9f" opacity=".45" />
    </g>

    <!-- 打开的书本 -->
    <g filter="url(#hi-soft)">
      <path d="M320 470c-26-18-58-22-84-18v-62c26-4 58 0 84 18z" fill="url(#hi-book)" />
      <path d="M320 470c26-18 58-22 84-18v-62c-26-4-58 0-84 18z" fill="url(#hi-book)" />
      <path d="M320 408v62" stroke="#c3cde8" stroke-width="4" stroke-linecap="round" />
      <g stroke="#a8b9ff" stroke-width="4" stroke-linecap="round" opacity=".85">
        <path d="M254 410h44" />
        <path d="M254 424h44" />
        <path d="M254 438h32" />
        <path d="M342 410h44" />
        <path d="M342 424h44" />
        <path d="M354 438h32" />
      </g>
    </g>

    <!-- 六大模块图标环绕 -->
    <!-- 阅读流畅性 -->
    <g transform="translate(126, 214)">
      <circle r="30" fill="#ffffff" filter="url(#hi-soft)" />
      <rect x="-14" y="-12" width="28" height="24" rx="4" fill="none" stroke="#4c6fff" stroke-width="3.4" />
      <path d="M0 -12v24" stroke="#4c6fff" stroke-width="3.4" stroke-linecap="round" />
    </g>
    <!-- 朗读流畅性（麦克风） -->
    <g transform="translate(180, 106)">
      <circle r="28" fill="#ffffff" filter="url(#hi-soft)" />
      <rect x="-7" y="-15" width="14" height="20" rx="7" fill="#f0743a" />
      <path d="M-12 2a12 12 0 0 0 24 0" fill="none" stroke="#f0743a" stroke-width="3.4" stroke-linecap="round" />
      <path d="M0 14v6" stroke="#f0743a" stroke-width="3.4" stroke-linecap="round" />
    </g>
    <!-- 注意力筛查（靶心） -->
    <g transform="translate(462, 96)">
      <circle r="28" fill="#ffffff" filter="url(#hi-soft)" />
      <circle r="14" fill="none" stroke="#12b3a8" stroke-width="3.4" />
      <circle r="5.5" fill="#12b3a8" />
    </g>
    <!-- 计算流畅性 -->
    <g transform="translate(524, 244)">
      <circle r="30" fill="#ffffff" filter="url(#hi-soft)" />
      <path d="M-14 -6h16M-6 -14v16" stroke="#8b5cf6" stroke-width="3.4" stroke-linecap="round" />
      <path d="M0 10h16" stroke="#8b5cf6" stroke-width="3.4" stroke-linecap="round" />
      <path d="M6 4l10 12M16 4L6 16" stroke="#8b5cf6" stroke-width="3.4" stroke-linecap="round" opacity=".0" />
      <path d="M-14 8h10" stroke="#8b5cf6" stroke-width="3.4" stroke-linecap="round" />
    </g>
    <!-- 识字量（汉字） -->
    <g transform="translate(96, 348)">
      <circle r="27" fill="#ffffff" filter="url(#hi-soft)" />
      <text x="0" y="8" text-anchor="middle" font-size="26" font-weight="700" fill="#e0518c"
            font-family="'Kaiti SC','KaiTi',serif">字</text>
    </g>
    <!-- 图形推理（拼图/几何） -->
    <g transform="translate(534, 372)">
      <circle r="28" fill="#ffffff" filter="url(#hi-soft)" />
      <rect x="-14" y="-14" width="12" height="12" rx="2.5" fill="#f0a92c" />
      <circle cx="8" cy="-8" r="6.4" fill="#f0a92c" opacity=".55" />
      <path d="M-14 4h12l-6 12z" fill="#f0a92c" opacity=".75" />
      <rect x="2" y="2" width="12" height="12" rx="2.5" fill="none" stroke="#f0a92c" stroke-width="3" />
    </g>

    <!-- 星点装饰 -->
    <g fill="#4c6fff" opacity=".5">
      <path d="M424 168l4 10 10 4-10 4-4 10-4-10-10-4 10-4z" />
      <path d="M226 296l3 7 7 3-7 3-3 7-3-7-7-3 7-3z" opacity=".7" />
    </g>
    <g fill="#f0a92c" opacity=".65">
      <path d="M470 306l3.5 8.5 8.5 3.5-8.5 3.5-3.5 8.5-3.5-8.5-8.5-3.5 8.5-3.5z" />
    </g>
  </svg>
</template>

<style scoped>
.hero-svg {
  width: 100%;
  height: auto;
  max-width: 560px;
  display: block;
  filter: drop-shadow(0 24px 48px rgba(44, 55, 82, .10));
}
</style>
