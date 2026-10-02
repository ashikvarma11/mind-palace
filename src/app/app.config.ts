import {
  ApplicationConfig,
  CSP_NONCE,
  DOCUMENT,
  inject,
  provideBrowserGlobalErrorListeners,
} from '@angular/core';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    {
      provide: CSP_NONCE,
      useFactory: () =>
        inject(DOCUMENT).querySelector<HTMLStyleElement>('#native-style-nonce')?.nonce || null,
    },
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes, withComponentInputBinding()),
  ],
};
