import { TestBed } from '@angular/core/testing';

import { HabitComponent } from './habit';

describe('HabitComponent', () => {
	beforeEach(async () => {
		await TestBed.configureTestingModule({
			imports: [HabitComponent]
		}).compileComponents();
	});

	it('should create', () => {
		const fixture = TestBed.createComponent(HabitComponent);
		const component = fixture.componentInstance;
		expect(component).toBeTruthy();
	});
});
