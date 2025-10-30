export const truncateFileName = (fileName: string, maxLength: number = 25): string => {
  if (fileName.length <= maxLength) return fileName
  const ext = fileName.split('.').pop() || ''
  const name = fileName.slice(0, -(ext.length + 1))
  // Calculate available space for the name (maxLength - extension length - dot - ellipsis)
  const availableSpace = maxLength - ext.length - 1 - 3
  if (availableSpace <= 0) {
    // If there's not enough space, return just truncated name with ellipsis
    return fileName.slice(0, maxLength - 3) + '...'
  }
  // Split the available space evenly for start and end of filename
  const halfSpace = Math.floor(availableSpace / 2)
  return `${name.slice(0, halfSpace)}...${name.slice(-halfSpace)}.${ext}`
}
