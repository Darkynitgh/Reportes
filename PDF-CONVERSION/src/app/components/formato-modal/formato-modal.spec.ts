import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FormatoModal } from './formato-modal';

describe('FormatoModal', () => {
  let component: FormatoModal;
  let fixture: ComponentFixture<FormatoModal>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FormatoModal],
    }).compileComponents();

    fixture = TestBed.createComponent(FormatoModal);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
