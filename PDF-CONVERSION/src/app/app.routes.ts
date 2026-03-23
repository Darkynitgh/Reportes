import { Routes } from '@angular/router';
import { LoginComponent } from './auth/login/login';
import { Dashboard } from './dashboard/dashboard';
import { ConfigurarPersonalizado } from './pages/configurar-personalizado/configurar-personalizado';

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'dashboard', component: Dashboard },
  { path: 'configurar-personalizado', component: ConfigurarPersonalizado},
];