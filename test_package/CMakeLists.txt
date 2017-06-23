project(PackageTest CXX)
cmake_minimum_required(VERSION 2.7.0)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

find_package(Boost COMPONENTS regex)

IF(Boost_FOUND)
    include_directories(${Boost_INCLUDE_DIRS})
    ADD_EXECUTABLE(lambda lambda.cpp)
ELSE()
    MESSAGE(FATAL_ERROR "ERROR! BOOST NOT FOUND!")
ENDIF()
