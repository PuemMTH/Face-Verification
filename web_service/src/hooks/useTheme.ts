import { useEffect } from 'react';
import { useLocalStorage } from 'usehooks-ts';

type Theme = 'light' | 'dark';

export const useTheme = () => {
  const [theme, setTheme] = useLocalStorage<Theme>('theme', 'light', {
    serializer: (value: Theme) => value,
    deserializer: (value: string) => value as Theme,
  });

  const toggleTheme = () => {
    setTheme(prevTheme => prevTheme === 'light' ? 'dark' : 'light');
  };

  useEffect(() => {
    const htmlElement = document.documentElement;
    htmlElement.setAttribute('data-theme', theme);
  }, [theme]);

  return {
    theme,
    toggleTheme,
  };
};