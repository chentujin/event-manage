/**
 * 日期格式化工具函数
 */

/**
 * 格式化日期时间
 * @param {string|Date} dateTime - 日期时间
 * @param {string} format - 格式模板，默认 'YYYY-MM-DD HH:mm:ss'
 * @returns {string} 格式化后的日期时间字符串
 */
export function formatDateTime(dateTime, format = 'YYYY-MM-DD HH:mm:ss') {
  if (!dateTime) return '-'
  
  const date = new Date(dateTime)
  if (isNaN(date.getTime())) return '-'
  
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  
  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
}

/**
 * 格式化日期
 * @param {string|Date} date - 日期
 * @param {string} format - 格式模板，默认 'YYYY-MM-DD'
 * @returns {string} 格式化后的日期字符串
 */
export function formatDate(date, format = 'YYYY-MM-DD') {
  return formatDateTime(date, format)
}

/**
 * 格式化时间
 * @param {string|Date} time - 时间
 * @param {string} format - 格式模板，默认 'HH:mm:ss'
 * @returns {string} 格式化后的时间字符串
 */
export function formatTime(time, format = 'HH:mm:ss') {
  return formatDateTime(time, format)
}

/**
 * 获取相对时间
 * @param {string|Date} dateTime - 日期时间
 * @returns {string} 相对时间描述
 */
export function getRelativeTime(dateTime) {
  if (!dateTime) return '-'
  
  const date = new Date(dateTime)
  if (isNaN(date.getTime())) return '-'
  
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  // 转换为秒
  const seconds = Math.floor(diff / 1000)
  
  if (seconds < 60) {
    return '刚刚'
  }
  
  // 转换为分钟
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) {
    return `${minutes}分钟前`
  }
  
  // 转换为小时
  const hours = Math.floor(minutes / 60)
  if (hours < 24) {
    return `${hours}小时前`
  }
  
  // 转换为天
  const days = Math.floor(hours / 24)
  if (days < 7) {
    return `${days}天前`
  }
  
  // 超过一周显示具体日期
  return formatDate(date)
}

/**
 * 检查日期是否过期
 * @param {string|Date} date - 日期
 * @returns {boolean} 是否过期
 */
export function isOverdue(date) {
  if (!date) return false
  
  const targetDate = new Date(date)
  if (isNaN(targetDate.getTime())) return false
  
  const now = new Date()
  return targetDate.getTime() < now.getTime()
}

/**
 * 计算时间差
 * @param {string|Date} startTime - 开始时间
 * @param {string|Date} endTime - 结束时间
 * @returns {object} 时间差对象 {days, hours, minutes, seconds}
 */
export function getTimeDiff(startTime, endTime) {
  if (!startTime || !endTime) return null
  
  const start = new Date(startTime)
  const end = new Date(endTime)
  
  if (isNaN(start.getTime()) || isNaN(end.getTime())) return null
  
  const diff = end.getTime() - start.getTime()
  
  if (diff < 0) return null
  
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  
  return {
    days: days,
    hours: hours % 24,
    minutes: minutes % 60,
    seconds: seconds % 60,
    totalSeconds: seconds
  }
}

/**
 * 格式化持续时间
 * @param {string|Date} startTime - 开始时间
 * @param {string|Date} endTime - 结束时间
 * @returns {string} 格式化的持续时间
 */
export function formatDuration(startTime, endTime) {
  const diff = getTimeDiff(startTime, endTime)
  
  if (!diff) return '-'
  
  if (diff.days > 0) {
    return `${diff.days}天${diff.hours}小时${diff.minutes}分钟`
  } else if (diff.hours > 0) {
    return `${diff.hours}小时${diff.minutes}分钟`
  } else if (diff.minutes > 0) {
    return `${diff.minutes}分钟${diff.seconds}秒`
  } else {
    return `${diff.seconds}秒`
  }
}