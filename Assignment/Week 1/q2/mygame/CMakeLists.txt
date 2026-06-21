cmake_minimum_required(VERSION 3.22)
project(MyGame CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Reuse system include and lib paths, assuming /usr/local/{include,lib}
include_directories(/usr/local/include)
link_directories(/usr/local/lib)

# mygamestatic
add_executable(mygamestatic mygame.cpp)
target_link_libraries(mygamestatic PRIVATE MyEngineStatic)

# mygamedynamic
add_executable(mygamedynamic mygame.cpp)
target_link_libraries(mygamedynamic PRIVATE MyEngineDynamic)