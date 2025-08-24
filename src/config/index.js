/**
 * 环境配置文件
 * 根据不同环境配置API地址和其他设置
 */

// 环境类型
export const ENV = {
  DEVELOPMENT: 'development',
  STAGING: 'staging',
  PRODUCTION: 'production'
}

// 当前环境 - 默认为临时部署环境
export const CURRENT_ENV = import.meta.env.VITE_APP_ENV || ENV.STAGING

// 环境配置
const envConfig = {
  [ENV.DEVELOPMENT]: {
    API_BASE_URL: 'http://localhost:3000',
    WS_BASE_URL: 'ws://localhost:3000',
    DEBUG: true
  },
  [ENV.STAGING]: {
    API_BASE_URL: 'https://eduscreenapi.psyventures.cn',
    WS_BASE_URL: 'wss://eduscreenapi.psyventures.cn',
    DEBUG: true
  },
  [ENV.PRODUCTION]: {
    API_BASE_URL: 'https://eduscreenapi.psyventures.cn',
    WS_BASE_URL: 'wss://eduscreenapi.psyventures.cn',
    DEBUG: false
  }
}

// 获取当前环境配置
export const config = envConfig[CURRENT_ENV]

// API相关配置
export const API_CONFIG = {
  BASE_URL: config.API_BASE_URL,
  PREFIX: '/api',
  TIMEOUT: 10000
}

// WebSocket配置
export const WS_CONFIG = {
  BASE_URL: config.WS_BASE_URL
}

// 调试配置
export const DEBUG = config.DEBUG

// 完整的API URL
export const API_URL = `${API_CONFIG.BASE_URL}${API_CONFIG.PREFIX}`

console.log(`当前环境: ${CURRENT_ENV}`)
console.log(`API地址: ${API_URL}`)