import { reactive } from 'vue'
import { ApiService } from '@/services/api'

const budgetStore = reactive({
  usage: 0.0
})

export function useBudgetStore() {
  const api = new ApiService()

  async function updateBudget() {
    budgetStore.usage = (await api.findBudgetUsage()).usagePercent
  }

  return { budgetStore, updateBudget }
}
