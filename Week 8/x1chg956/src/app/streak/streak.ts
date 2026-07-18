import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

import { HabitStreak } from '../habit/habit.model';
import { HabitService } from '../habit/habit.service';

@Component({
	selector: 'app-streak',
	standalone: true,
	imports: [CommonModule, RouterLink],
	templateUrl: './streak.html',
	styleUrl: './streak.css'
})
export class StreakComponent implements OnInit {
	streaks: HabitStreak[] = [];
	errorMessage: string | null = null;

	constructor(private habitService: HabitService) { }

	ngOnInit(): void {
		this.loadStreaks();
	}

	loadStreaks(): void {
		this.errorMessage = null;
		this.habitService.getStreaks().subscribe({
			next: (response) => {
				this.streaks = response;
			},
			error: (err) => {
				this.errorMessage = 'Failed to load streaks. Please try again.';
				console.error(err);
			}
		});
	}
}