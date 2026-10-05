import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { App } from './app.component';
describe('Mind Palace shell', () => {
  it('renders honest prototype status and accessible navigation', async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideRouter([])],
    }).compileComponents();
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const element = fixture.nativeElement as HTMLElement;
    expect(element.textContent).toContain('Desktop vault unavailable in browser');
    expect(element.querySelector('nav')?.getAttribute('aria-label')).toBe('Main navigation');
    expect(element.querySelectorAll('nav a')).toHaveLength(8);
  });
});
