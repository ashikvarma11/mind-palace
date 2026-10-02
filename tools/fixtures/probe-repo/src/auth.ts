import { MemoryStore } from './store';

export class AuthService {
  constructor(private store: MemoryStore) {}

  remember(): string {
    return this.store.save('synthetic evidence');
  }
}
