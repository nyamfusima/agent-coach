// Agent profile persisted in localStorage (no passwords for V1).
const KEY = 'agentProfile'

export function loadProfile() {
  try {
    const raw = localStorage.getItem(KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function saveProfile(profile) {
  localStorage.setItem(KEY, JSON.stringify(profile))
}

export function clearProfile() {
  localStorage.removeItem(KEY)
}
