# CSS Structure

## Shared Styles
- `app.css` - Global application styles
- `index.css` - Root styles and CSS variables
- `legacy.css` - Legacy styles from Flask app (to be refactored)

## Feature Styles

### Auth
- `auth.css` - Common authentication styles
- `login.css` - Login page specific styles
- `register.css` - Registration page specific styles

### Dashboard
- `dashboard.css` - Dashboard layout and component styles

### Tips
- `tip.css` - Tip page and component styles

## Style Guidelines
1. Use CSS modules for component-specific styles
2. Keep global styles in shared/styles
3. Feature-specific styles should be in their respective feature folders
4. Use CSS variables for consistent theming
5. Follow BEM naming convention for legacy CSS
6. New components should use Tailwind CSS utilities 