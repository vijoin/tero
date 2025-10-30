import moment from 'moment'

const getLast30Days = () => {
  return moment().subtract(30, 'days').startOf('day').toDate()
}

export const useDateRange = () => {
  const fromDate = getLast30Days()
  const toDate = moment().endOf('day').toDate()

  return { fromDate, toDate }
}
