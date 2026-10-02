import { CSP_NONCE } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { appConfig } from './app.config';

describe('Native style nonce', () => {
  afterEach(() => document.querySelector('#native-style-nonce')?.remove());

  it('passes the response-provided nonce to Angular', () => {
    const marker = document.createElement('style');
    marker.id = 'native-style-nonce';
    marker.nonce = 'test-response-nonce';
    document.head.append(marker);
    TestBed.configureTestingModule({ providers: appConfig.providers });
    expect(TestBed.inject(CSP_NONCE)).toBe('test-response-nonce');
  });

  it('does not fabricate a nonce outside the native response', () => {
    TestBed.configureTestingModule({ providers: appConfig.providers });
    expect(TestBed.inject(CSP_NONCE)).toBeNull();
  });
});
