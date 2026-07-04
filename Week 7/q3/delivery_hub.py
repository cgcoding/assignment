"""Q3 - Optimizing Delivery Hubs (vectorized K-Means).

Implements K-Means with pure NumPy vectorization: no for loops, list
comprehensions, or any iteration over the dataset or the clusters. The only
loop is the `while True:` convergence loop in kmeans().
"""

import time

import numpy as np


def load_data(data_path):
    """Read the 2D comma-separated file and return an N x 2 numpy array."""
    return np.loadtxt(data_path, delimiter=",", ndmin=2)


def initialise_centers(data, K, init_centers=None):
    """K random data points without replacement, or the provided centers."""
    if init_centers is None:
        indices = np.random.choice(data.shape[0], size=K, replace=False)
        return data[indices].astype(float)
    return np.asarray(init_centers, dtype=float)


def initialise_labels(data):
    """1D zeros array of size N."""
    return np.zeros(data.shape[0], dtype=int)


def calculate_distances(data, centers):
    """Euclidean distance from each of N points to each of K hubs (N x K).

    Broadcasting: data reshaped to (N, 1, 2) against centers (K, 2) yields
    an (N, K, 2) difference tensor; the norm over the last axis gives (N, K).
    """
    diff = data[:, np.newaxis, :] - centers[np.newaxis, :, :]
    return np.sqrt(np.sum(diff**2, axis=2))


def update_labels(distances):
    """Assign each delivery point to its nearest hub (array of size N)."""
    return np.argmin(distances, axis=1)


def update_centers(data, labels, K):
    """Move each hub to the mean of its assigned points.

    A Boolean mask of shape (K, N) compares labels to np.arange(K); its dot
    product with the data matrix sums member coordinates per cluster, and a
    per-cluster member count normalizes to the mean. Empty clusters keep a
    zero count guarded to 1 to avoid division by zero (their center becomes
    the origin of the mask sum, i.e. 0/1 = 0; they are then re-labelled on
    the next assignment step).
    """
    mask = labels == np.arange(K)[:, np.newaxis]  # (K, N) boolean
    counts = mask.sum(axis=1, keepdims=True)  # (K, 1)
    sums = mask @ data  # (K, 2)
    return sums / np.maximum(counts, 1)


def check_termination(labels1, labels2):
    """True when no label changed from the previous iteration."""
    return np.array_equal(labels1, labels2)


def kmeans(data_path, K, init_centers=None):
    """Full K-Means. Returns (final_centers, labels, execution_time)."""
    start = time.perf_counter()

    data = load_data(data_path)
    centers = initialise_centers(data, K, init_centers)
    labels = initialise_labels(data)

    while True:
        distances = calculate_distances(data, centers)
        new_labels = update_labels(distances)
        centers = update_centers(data, new_labels, K)
        if check_termination(labels, new_labels):
            break
        labels = new_labels

    exec_time = time.perf_counter() - start
    return centers, labels, exec_time


if __name__ == "__main__":
    # Sample execution from the assignment (deterministic initial centers).
    init_centers = [[1.0, 1.0], [8.0, 8.0]]
    final_centers, labels, exec_time = kmeans(
        "delivery_locations.txt", 2, init_centers
    )

    print("Final Centers:")
    print(final_centers)
    print("\nLabels:")
    print(labels)
    print(f"\nExecution Time: {exec_time:.4f} seconds")
