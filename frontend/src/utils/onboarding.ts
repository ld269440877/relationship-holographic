let onboardingCompletedMemory = false
const onboardingKey = 'hasCompletedOnboarding'

export function hasCompletedOnboarding(): boolean {
  if (onboardingCompletedMemory) return true
  try {
    if (localStorage.getItem(onboardingKey) === 'true') return true
  } catch {
    // localStorage may be unavailable in privacy or embedded browser contexts.
  }
  try {
    if (sessionStorage.getItem(onboardingKey) === 'true') return true
  } catch {
    // sessionStorage can be disabled by the same policy.
  }
  try {
    return document.cookie.split('; ').some((item) => item === `${onboardingKey}=true`)
  } catch {
    return false
  }
}

export function markOnboardingCompleted(): void {
  onboardingCompletedMemory = true
  try {
    localStorage.setItem(onboardingKey, 'true')
  } catch {
    // 隐私模式或测试浏览器可能禁用 localStorage。
  }
  try {
    sessionStorage.setItem(onboardingKey, 'true')
  } catch {
    // sessionStorage 也可能不可用。
  }
  try {
    document.cookie = `${onboardingKey}=true; path=/; max-age=31536000; SameSite=Lax`
  } catch {
    // cookie 兜底失败时仍保留内存标记。
  }
}
