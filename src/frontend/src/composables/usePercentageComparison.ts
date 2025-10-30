export function usePercentageComparison() {
  const previousPercentageComparison = (value: number, previousValue: number) => {
    if (previousValue === 0) {
      return value > 0 ? 100 : 0
    }

    const percentage = ((value - previousValue) * 100) / previousValue
    return parseFloat(percentage.toFixed(1))
  }

  return {
    previousPercentageComparison
  }
}