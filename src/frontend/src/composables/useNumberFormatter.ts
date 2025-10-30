import { useI18n } from 'vue-i18n';

export function useNumberFormatter() {
  const { locale } = useI18n({ useScope: 'global' });

  const createFormatter = (options: Intl.NumberFormatOptions) => {
    return new Intl.NumberFormat(locale.value, options);
  }

  const formatCompactNumber = (value: number, decimals: number = 1) => {
    const formattedNumber = createFormatter({
      notation: 'compact',
      maximumFractionDigits: decimals,
    }).format(value)

    return formattedNumber.replace('mil M', 'B').replace('millones', 'M').replace('mil', 'K');
  }

  return {
    formatCompactNumber,
  };
}