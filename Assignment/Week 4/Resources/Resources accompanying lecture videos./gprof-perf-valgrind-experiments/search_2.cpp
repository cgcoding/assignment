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

	if (arr[low] > arr[right])
		std::swap(arr[low], arr[right]);

	quicksort(arr, low, right - 1);
	quicksort(arr, right + 1, high);
}

// Recursive binary search
int binary_search(const std::vector<int> &vec, int low, int high, int target)
{
	if (low > high)
		return -1;

	int mid = (low + high) / 2;
	if (vec[mid] == target)
		return mid;
	else if (vec[mid] > target)
		return binary_search(vec, low, mid - 1, target);
	else
		return binary_search(vec, mid + 1, high, target);
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

	int index = binary_search(vec, 0, vec.size() - 1, target);
	if (index != -1)
		std::cout << "Found " << target << " at index " << index << endl;
	else
		std::cout << target << " not found in the array.\n";
	std::cout << "Count: " << count << "\n";
	return 0;
}
