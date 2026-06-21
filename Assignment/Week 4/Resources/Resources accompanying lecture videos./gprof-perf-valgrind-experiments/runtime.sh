echo "Original"
g++ -O0 -o search_1 search_1.cpp
# warm up 3 runs, then measure 10 runs
hyperfine --warmup 3 ./search_1

echo "-------------------------------------------"

echo "Optimization 1: Vector to array"
g++ -O0 -o search_2 search_2.cpp
hyperfine --warmup 3 ./search_2

echo "-------------------------------------------"

echo "Optimization 2: Reduce Recursive call overhead"
g++ -O0 -o search_3 search_3.cpp
hyperfine --warmup 3 ./search_3

echo "-------------------------------------------"

echo "Optimization 3: Inline swap function"
g++ -O0 -o search_4 search_4.cpp
hyperfine --warmup 3 ./search_4		

echo "-------------------------------------------"

echo "Optimization 4: Iterative Binary search"
g++ -O0 -o search_5 search_5.cpp
hyperfine --warmup 3 ./search_5

echo "-------------------------------------------"

echo "Optimization 4: Using -O3"
g++ -O3 -o search_5 search_5.cpp
hyperfine --warmup 3 ./search_5

echo "-------------------------------------------"

echo "Optimization 4: Using -O3 on the original"
g++ -O3 -o search_1 search_1.cpp
hyperfine --warmup 3 ./search_1

