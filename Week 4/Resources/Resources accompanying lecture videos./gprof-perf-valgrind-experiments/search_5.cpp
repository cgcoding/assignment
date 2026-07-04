#include <iostream>
#include <vector>
#include <cstdlib>
#include <ctime>
long count = 0;
long int data_size = 10000000;
// Recursive quicksort
using namespace std;
void quicksort(int *arr, int low, int high)
{
	++count;
	while (low < high)
	{
		// initialize for partition
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
			{
				// inline swap
				int tmp = arr[left];
				arr[left] = arr[right];
				arr[right] = tmp;
			}
		}

		// final pivot placement
		if (arr[low] > arr[right])
		{
			int tmp = arr[low];
			arr[low] = arr[right];
			arr[right] = tmp;
		}

		// recurse on the smaller half, loop on the larger
		if (right - low < high - right)
		{
			quicksort(arr, low, right - 1);
			low = right + 1;
		}
		else
		{
			quicksort(arr, right + 1, high);
			high = right - 1;
		}
	}
}

// Iterative binary search

int binary_search(const int *arr, int low, int high, int target)
{
	while (low <= high)
	{
		// Prevent overflow
		int mid = low + (high - low) / 2;
		int value = arr[mid];

		if (value == target)
			return mid;
		else if (value > target)
			high = mid - 1;
		else
			low = mid + 1;
	}
	return -1;
}
int main()
{
	std::vector<int> vec(data_size);
	std::srand(42);		// Seed for random number generation
	int target = 13456; // Target value to search for
	for (int i = 0; i < data_size; ++i)
		vec[i] = std::rand() % 1000000;
	vec[999] = target; // Ensure the target is in the array

	quicksort(vec.data(), 0, vec.size() - 1);

	int index = binary_search(vec.data(), 0, vec.size() - 1, target);
	if (index != -1)
		cout << "Found " << target << " at index " << index << endl;
	else
		std::cout << target << " not found in the array.\n";
	cout << "Count: " << count << "\n";
	return 0;
}
