#  7.5SDK
set (CMAKE_SYSTEM_NAME ORBIS)
set (CMAKE_SYSTEM_VERSION 7.5)
set (ORBIS_PS4 True)



set (My_ORBIS_SDK_Path $ENV{SCE_ORBIS_SDK_DIR})
string(REPLACE "\\" "/" My_ORBIS_SDK_Path "${My_ORBIS_SDK_Path}")

include (CMakeForceCompiler)
set (CMAKE_C_COMPILER "${My_ORBIS_SDK_Path}/host_tools/bin/orbis-clang.exe" CACHE STRING INTERNAL FORCE)
set (CMAKE_CXX_COMPILER "${My_ORBIS_SDK_Path}/host_tools/bin/orbis-clang++.exe" CACHE STRING INTERNAL FORCE)
set (CMAKE_NM  "${My_ORBIS_SDK_Path}/host_tools/bin/orbis-nm.exe" CACHE STRING INTERNAL FORCE)


set (CMAKE_CXX_COMPILER_WORKS TRUE)
set (CMAKE_C_COMPILER_WORKS TRUE)


set (CMAKE_GENERATOR_PLATFORM  "ORBIS")
set (CMAKE_GENERATOR_TOOLSET  "Clang")
