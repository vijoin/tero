export const useDebounce = (fn: Function) => {
  const searchDebounceTimeMs = 500;
  let searchTimeout: number | null = null;
  
  return () => {
    if(searchTimeout) {
      window.clearTimeout(searchTimeout);
    }
    return searchTimeout = window.setTimeout(() => {
      fn();
    }, searchDebounceTimeMs);
  };
};