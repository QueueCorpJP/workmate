import React from 'react';
import { AdminPanel } from './components/admin';

// Register Chart.js 
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
} from 'chart.js';

// Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

const AdminPanelPage: React.FC = () => {
  return <AdminPanel />;
};

export default AdminPanelPage;