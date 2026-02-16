import { useTheme } from '@shared/context/ThemeContext';
import './ThemeToggle.css';

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <div
      className="theme-toggle"
      onClick={toggleTheme}
      title="Toggle light/dark theme"
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && toggleTheme()}
    >
      <span className="toggle-icon">{isDark ? '☀️' : '🌙'}</span>
      <div className="toggle-track">
        <div className="toggle-thumb" />
      </div>
      <span className="toggle-label">{isDark ? 'Light' : 'Dark'}</span>
    </div>
  );
}
