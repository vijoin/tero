import { ApiService, Role, UserProfile } from '@/services/api'

export async function loadUserProfile(): Promise<UserProfile | null> {
    const api = new ApiService()
    const profile: UserProfile = await api.findUserProfile()
    return profile
}