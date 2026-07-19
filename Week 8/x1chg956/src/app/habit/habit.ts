import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { HabitService } from './habit.service';
import { Habit, Frequency } from './habit.model';

@Component({
	selector: 'app-habit',
	standalone: true,
	imports: [CommonModule, FormsModule, RouterLink],
	templateUrl: './habit.html',
	styleUrl: './habit.css'
})
export class HabitComponent implements OnInit {
	habits: Habit[] = [];
	newHabit: { name: string; frequency: Frequency } = { name: '', frequency: 'Daily' };
	errorMessage: string | null = null;

	constructor(private habitService: HabitService, private router: Router, private cdr: ChangeDetectorRef) { }

	ngOnInit(): void {
		this.habitService.getHabits().subscribe({
			next: (habits) => {
				this.habits = habits;
				this.cdr.markForCheck();
			},
			error: (err) => {
				this.errorMessage = 'Failed to load habits.';
				console.error(err);
				this.cdr.markForCheck();
			}
		});
	}

	onSubmit(): void {
		if (!this.newHabit.name.trim()) return;
		this.habitService.createHabit(this.newHabit).subscribe({
			next: (habit) => {
				this.habits.push(habit);
				this.newHabit = { name: '', frequency: 'Daily' };
				this.cdr.markForCheck();
			},
			error: (err) => {
				this.errorMessage = 'Failed to create habit.';
				console.error(err);
				this.cdr.markForCheck();
			}
		});
	}

	completeHabit(habit: Habit): void {
		this.habitService.completeHabit(habit.habitId, this.todayIso()).subscribe({
			next: () => {
				this.errorMessage = null;
				habit.completed = true;
				this.cdr.markForCheck();
			},
			error: (err) => {
				this.errorMessage = err.status === 409
					? `"${habit.name}" is already completed for this period.`
					: 'Failed to complete habit.';
				if (err.status === 409) {
					habit.completed = true;
				}
				console.error(err);
				this.cdr.markForCheck();
			}
		});
	}

	deleteHabit(habit: Habit): void {
		this.habitService.deleteHabit(habit.habitId).subscribe({
			next: () => {
				this.habits = this.habits.filter(h => h.habitId !== habit.habitId);
				this.cdr.markForCheck();
			},
			error: (err) => {
				this.errorMessage = 'Failed to delete habit.';
				console.error(err);
				this.cdr.markForCheck();
			}
		});
	}

	logout(): void {
		localStorage.removeItem('token');
		this.router.navigate(['/auth']);
	}

	private todayIso(): string {
		const d = new Date();
		const yyyy = d.getFullYear();
		const mm = String(d.getMonth() + 1).padStart(2, '0');
		const dd = String(d.getDate()).padStart(2, '0');
		return `${yyyy}-${mm}-${dd}`;
	}
}
