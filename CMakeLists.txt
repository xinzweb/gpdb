cmake_minimum_required(VERSION 3.6)
project(gpdb)

file(GLOB_RECURSE SRC_FILES
        "*.h"
        "*.c"
        "*.cpp"
        "*.cxx")

include_directories(src/include)

add_executable(gpdb ${SRC_FILES})
