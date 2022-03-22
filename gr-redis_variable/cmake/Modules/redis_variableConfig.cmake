INCLUDE(FindPkgConfig)
PKG_CHECK_MODULES(PC_REDIS_VARIABLE redis_variable)

FIND_PATH(
    REDIS_VARIABLE_INCLUDE_DIRS
    NAMES redis_variable/api.h
    HINTS $ENV{REDIS_VARIABLE_DIR}/include
        ${PC_REDIS_VARIABLE_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    REDIS_VARIABLE_LIBRARIES
    NAMES gnuradio-redis_variable
    HINTS $ENV{REDIS_VARIABLE_DIR}/lib
        ${PC_REDIS_VARIABLE_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/redis_variableTarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(REDIS_VARIABLE DEFAULT_MSG REDIS_VARIABLE_LIBRARIES REDIS_VARIABLE_INCLUDE_DIRS)
MARK_AS_ADVANCED(REDIS_VARIABLE_LIBRARIES REDIS_VARIABLE_INCLUDE_DIRS)
