import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import {
  LucideDynamicIcon,
  LucideCastle,
  LucideSun,
  LucideMessagesSquare,
  LucideGitBranch,
  LucideSparkles,
  LucideArrowRight,
  LucideNetwork,
  LucideSettings,
  LucideSearch,
  LucideShieldCheck,
} from '@lucide/angular';
import { WorkspaceStore } from './core/workspace-store';
import { LocalVault } from './core/local-vault';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, LucideDynamicIcon],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class App {
  readonly environmentLabel =
    '__TAURI_INTERNALS__' in globalThis ? 'Desktop prototype' : 'Browser prototype';
  readonly store = inject(WorkspaceStore);
  readonly vault = inject(LocalVault);
  readonly logoMissing = signal(false);
  readonly icons = { search: LucideSearch, shield: LucideShieldCheck };
  readonly navigation = [
    { path: '/welcome', title: 'Welcome', icon: LucideCastle },
    { path: '/today', title: 'Today', icon: LucideSun },
    { path: '/sessions', title: 'Sessions', icon: LucideMessagesSquare },
    { path: '/decisions', title: 'Decisions', icon: LucideGitBranch },
    { path: '/ask', title: 'Ask memory', icon: LucideSparkles },
    { path: '/resume', title: 'Resume work', icon: LucideArrowRight },
    { path: '/connections', title: 'Connections', icon: LucideNetwork },
    { path: '/settings', title: 'Settings', icon: LucideSettings },
  ];
}
