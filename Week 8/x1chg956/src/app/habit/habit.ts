import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { Habit, HabitFrequency, HabitCompletionIn } from './habit.model';
import { HabitService } from './habit.service';

@Component({
	selector: 'app-habit',
	standalone: true,
	imports: [CommonModule, FormsModule],
	templateUrl: './habit.html',
	styleUrl: './habit.css'
})
export class HabitComponent implements OnInit {
	habits: Habit[] = [];
	newHabit: { name: string; frequency: HabitFrequency } = {
		name: '',
		frequency: 'daily'
	};
	errorMessage: string | null = null;
	successMessage: string | null = null;

	constructor(private habitService: HabitService) { }

	ngOnInit(): void {
		this.getHabits();
	}

	getHabits(): void {
		this.errorMessage = null;
		this.habitService.getHabits().subscribe({
			next: (response) => {
				this.habits = response;
			},
			error: (err) => {
				this.errorMessage = 'Failed to load habits. Please login again.';
				console.error(err);
			}
		});
	}

	addHabit(): void {
		this.errorMessage = null;
		this.successMessage = null;

		const habitName = this.newHabit.name.trim();
		if (!habitName) {
			this.errorMessage = 'Habit name is required.';
			return;
		}

		this.habitService.addHabit({
			name: habitName,
			frequency: this.newHabit.frequency
		}).subscribe({
			next: (createdHabit) => {
				this.habits = [createdHabit, ...this.habits];
				this.newHabit = { name: '', frequency: 'daily' };
				this.successMessage = 'Habit added successfully.';
			},
			error: (err) => {
				this.errorMessage = 'Failed to add habit.';
				console.error(err);
			}
		});
	}

	deleteHabit(habitId: number): void {
		this.errorMessage = null;
		this.successMessage = null;

		this.habitService.deleteHabit(habitId).subscribe({
			next: () => {
				this.habits = this.habits.filter((habit) => habit.id !== habitId);
				this.successMessage = 'Habit deleted.';
			},
			error: (err) => {
				this.errorMessage = 'Failed to delete habit.';
				console.error(err);
			}
		});
	}

	markComplete(habitId: number): void {
		this.errorMessage = null;
		this.successMessage = null;

		const today = new Date().toISOString().split('T')[0];
		const payload: HabitCompletionIn = { completion_date: today };

		this.habitService.markComplete(habitId, payload).subscribe({
			next: () => {
				this.successMessage = 'Habit marked complete for today.';
			},
			error: (err) => {
				const backendMessage = err?.error?.detail;
				this.errorMessage = backendMessage || 'Failed to mark habit complete.';
				console.error(err);
			}
		});
	}
}
