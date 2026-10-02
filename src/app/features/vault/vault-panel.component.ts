import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { LocalVault } from '../../core/local-vault';

@Component({
  selector: 'app-vault-panel',
  imports: [FormsModule],
  templateUrl: './vault-panel.component.html',
  styleUrl: './vault-panel.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class VaultPanel {
  readonly vault = inject(LocalVault);
}
