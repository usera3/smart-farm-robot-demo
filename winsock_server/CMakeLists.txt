cmake_minimum_required(VERSION 3.10)
project(FarmServer)

# 设置C++标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Windows特定设置
if(WIN32)
    add_definitions(-D_WIN32_WINNT=0x0601)  # Windows 7+
    add_definitions(-DWIN32_LEAN_AND_MEAN)
    add_definitions(-D_WINSOCK_DEPRECATED_NO_WARNINGS)
endif()

# 查找Python
find_package(Python3 COMPONENTS Interpreter Development)
if(Python3_FOUND)
    include_directories(${Python3_INCLUDE_DIRS})
    link_directories(${Python3_LIBRARY_DIRS})
    message(STATUS "Python3 found: ${Python3_VERSION}")
    message(STATUS "Python3 include: ${Python3_INCLUDE_DIRS}")
    message(STATUS "Python3 libraries: ${Python3_LIBRARIES}")
else()
    message(WARNING "Python3 not found, Python integration will be disabled")
endif()

# 包含目录
include_directories(${CMAKE_CURRENT_SOURCE_DIR})

# 源文件
set(SERVER_SOURCES
    protocol.cpp
    FarmServer.cpp
    main.cpp
)

# 如果有Python集成
if(Python3_FOUND)
    list(APPEND SERVER_SOURCES PythonBridge.cpp)
endif()

# 创建可执行文件
add_executable(FarmServer ${SERVER_SOURCES})

# 链接库
if(WIN32)
    # Windows平台需要链接Winsock库
    target_link_libraries(FarmServer ws2_32)
    if(Python3_FOUND)
        target_link_libraries(FarmServer ${Python3_LIBRARIES})
    endif()
elseif(APPLE)
    # macOS平台使用BSD Socket，不需要额外链接库
    message(STATUS "Building for macOS - using BSD Socket")
    if(Python3_FOUND)
        target_link_libraries(FarmServer ${Python3_LIBRARIES})
    endif()
elseif(UNIX)
    # Linux平台
    message(STATUS "Building for Linux - using BSD Socket")
    target_link_libraries(FarmServer pthread)
    if(Python3_FOUND)
        target_link_libraries(FarmServer ${Python3_LIBRARIES})
    endif()
endif()

# 设置输出目录
set_target_properties(FarmServer PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)

# 安装规则
install(TARGETS FarmServer DESTINATION bin)

# 复制配置文件
configure_file(
    ${CMAKE_CURRENT_SOURCE_DIR}/server_config.json
    ${CMAKE_BINARY_DIR}/bin/server_config.json
    COPYONLY
)

# 打印构建信息
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ compiler: ${CMAKE_CXX_COMPILER}")
message(STATUS "C++ flags: ${CMAKE_CXX_FLAGS}")
