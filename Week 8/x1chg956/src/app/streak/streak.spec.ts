import { TestBed } from '@angular/core/testing';

import { StreakComponent } from './streak';

describe('StreakComponent', () => {
	beforeEach(async () => {
		await TestBed.configureTestingModule({
			imports: [StreakComponent]
		}).compileComponents();
	});

	it('should create', () => {
		const fixture = TestBed.createComponent(StreakComponent);
		const component = fixture.componentInstance;
		expect(component).toBeTruthy();
	});
});