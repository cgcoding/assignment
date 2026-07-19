import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';

import { HabitComponent } from './habit';

describe('HabitComponent', () => {
	let component: HabitComponent;
	let fixture: ComponentFixture<HabitComponent>;

	beforeEach(async () => {
		await TestBed.configureTestingModule({
			imports: [HabitComponent],
			providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])]
		})
			.compileComponents();

		fixture = TestBed.createComponent(HabitComponent);
		component = fixture.componentInstance;
		fixture.detectChanges();
	});

	it('should create', () => {
		expect(component).toBeTruthy();
	});
});
