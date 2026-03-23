import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ConfigurarPersonalizado } from './configurar-personalizado';

describe('ConfigurarPersonalizado', () => {
  let component: ConfigurarPersonalizado;
  let fixture: ComponentFixture<ConfigurarPersonalizado>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ConfigurarPersonalizado],
    }).compileComponents();

    fixture = TestBed.createComponent(ConfigurarPersonalizado);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
