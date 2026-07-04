#include <iostream>
#include <vector>
#include <cstdlib>
#include <ctime>
long count = 0;
// Recursive quicksort
void quicksort(std::vector<int> &arr, int low, int high)
{
	count++;
	if (low >= high)
		return;

	int pivot = arr[low];
	int left = low + 1;
	int right = high;

	while (left <= right)
	{
		while (left <= high && arr[left] <= pivot)
			left++;
		while (right > low && arr[right] > pivot)
			right--;

		if (left < right)
			std::swap(arr[left], arr[right]);
	}

	// Makes the algorithm stable by ensuring that the pivot is not moved if arr[right] is also equal to pivot
	if (arr[low] > arr[right])
		std::swap(arr[low], arr[right]);
    // [low,right-1] are all <= arr[right], [right+1,high] are all > arr[right], either of the two segments can be empty
	quicksort(arr, low, right - 1);
	quicksort(arr, right + 1, high);
}

// Recursive binary search
int binary_search(const std::vector<int> &arr, int low, int high, int target)
{
	if (low > high)
		return -1;

	int mid = (low + high) / 2;
	if (arr[mid] == target)
		return mid;
	else if (arr[mid] > target)
		return binary_search(arr, low, mid - 1, target);
	else
		return binary_search(arr, mid + 1, high, target);
}

/**
 * The main function generates a large array of random integers, sorts it using quicksort, performs a
 * binary search for a target value, and then outputs the index of the target value if found.
 *
 * @return The code snippet provided is a part of a program that generates a large array of random
 * integers, sorts the array using quicksort, and then performs a binary search to find a specific
 * target integer within the array. The target integer is set to 94984, and the program checks if this
 * target is present in the array.
 */
int main()
{
	std::vector<int> arr(10000000);
	std::srand(42); // Seed for random number generation
	for (int i = 0; i < 10000000; ++i)
		arr[i] = std::rand() % 100000000;
	arr[969784] = 94984; // Ensure the target is in the array
	int target = 94984;

	// std::cout << "Original array:\n";
	// for (int num : arr) std::cout << num << " ";
	// std::cout << "\n";

	quicksort(arr, 0, arr.size() - 1);

	// std::cout << "Sorted array:\n";
	// for (int num : arr) std::cout << num << " ";
	// std::cout << "\n";

	int index = binary_search(arr, 0, arr.size() - 1, target);
	if (index != -1)
		std::cout << "Found " << target << " at index " << index << ".\n";
	else
		std::cout << target << " not found in the array.\n";

	std::cout << "Count: " << count << "\n";

	return 0;
}
