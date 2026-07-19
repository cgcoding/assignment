export type Frequency = 'Daily' | 'Weekly';

export interface Habit {
	habitId: number;
	name: string;
	frequency: Frequency;
	completed: boolean;
}

export interface Completion {
	id: number;
	habitId: number;
	period_start: string;
}
