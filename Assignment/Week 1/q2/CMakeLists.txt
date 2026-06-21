cmake_minimum_required(VERSION 3.10)
project(Week1Project CXX)

set(CMAKE_CXX_STANDARD 17)
add_compile_options(-Wall -O2)

# 1. helloworld
add_executable(helloworld helloworld.cpp)

# 2. usespthread
add_executable(usespthread usespthread.cpp)
target_link_libraries(usespthread pthread)

# 3. myengine as static and shared libraries
add_library(MyEngineStatic STATIC myengine/myengine.cpp)
target_include_directories(MyEngineStatic PUBLIC myengine)

add_library(MyEngineDynamic SHARED myengine/myengine.cpp)
target_include_directories(MyEngineDynamic PUBLIC myengine)

# 4. mygamestatic -- links against the static library
add_executable(mygamestatic mygame/mygame.cpp)
target_link_libraries(mygamestatic MyEngineStatic)

# 5. mygamedynamic -- links against the shared library
add_executable(mygamedynamic mygame/mygame.cpp)
target_link_libraries(mygamedynamic MyEngineDynamic)

# 6. install targets
install(TARGETS helloworld usespthread mygamestatic mygamedynamic
        RUNTIME DESTINATION bin)
install(TARGETS MyEngineStatic MyEngineDynamic
        ARCHIVE DESTINATION lib
        LIBRARY DESTINATION lib)
