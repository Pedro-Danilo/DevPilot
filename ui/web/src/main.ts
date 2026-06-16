import { renderDashboard } from './pages/Dashboard';
import './styles.css';

const root = document.querySelector<HTMLElement>('#app');

if (!root) {
  throw new Error('No se encontró el contenedor #app para DevPilot Web UI.');
}

renderDashboard(root);
