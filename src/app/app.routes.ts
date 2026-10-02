import { Routes } from '@angular/router';
import { PageKey } from './core/workspace-store';
const pages: readonly PageKey[] = [
  'welcome',
  'today',
  'sessions',
  'decisions',
  'ask',
  'resume',
  'connections',
  'settings',
];
export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'welcome' },
  ...pages.map((page) => ({
    path: page,
    title: `Mind Palace · ${page === 'ask' ? 'Ask memory' : page.charAt(0).toUpperCase() + page.slice(1)}`,
    data: { page },
    loadComponent: () =>
      import('./features/workspace/workspace-page.component').then((m) => m.WorkspacePage),
  })),
  { path: '**', redirectTo: 'welcome' },
];
